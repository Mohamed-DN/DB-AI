import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Cpu } from 'lucide-react';
import { useMutation, useQuery } from '@tanstack/react-query';
import * as api from '../../services/api';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
}

export default function AIChat() {
    const [messages, setMessages] = useState<Message[]>([
        {
            role: 'assistant',
            content: 'Ciao! Sono l\'assistente AI di Nexi CMDB. Posso aiutarti con informazioni sui database, alert di sistema, o qualsiasi domanda sull\'infrastruttura.',
            timestamp: new Date(),
        },
    ]);
    const [input, setInput] = useState('');
    const [selectedModel, setSelectedModel] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const { data: currentModel } = useQuery({
        queryKey: ['currentModel'],
        queryFn: api.getCurrentModel,
    });

    const { data: gpuStatus } = useQuery({
        queryKey: ['gpuStatus'],
        queryFn: api.getGpuStatus,
        refetchInterval: 5000,
    });

    const sendMessageMutation = useMutation({
        mutationFn: ({ message, model }: { message: string; model?: string }) => api.sendChatMessage(message, model),
        onSuccess: (response) => {
            setMessages((prev) => [
                ...prev,
                {
                    role: 'assistant',
                    content: typeof response === 'string' ? response : JSON.stringify(response),
                    timestamp: new Date(),
                },
            ]);
        },
        onError: (error) => {
            setMessages((prev) => [
                ...prev,
                {
                    role: 'assistant',
                    content: `Errore: ${String(error)}`,
                    timestamp: new Date(),
                },
            ]);
        },
    });

    const switchModelMutation = useMutation({
        mutationFn: api.switchModel,
        onError: (error) => {
            setMessages((prev) => [
                ...prev,
                {
                    role: 'assistant',
                    content: `Model switch failed: ${String(error)}`,
                    timestamp: new Date(),
                },
            ]);
        },
    });

    const handleSend = () => {
        if (!input.trim()) return;

        setMessages((prev) => [
            ...prev,
            { role: 'user', content: input, timestamp: new Date() },
        ]);

        sendMessageMutation.mutate({ message: input, model: selectedModel || currentModel?.model });
        setInput('');
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const { data: llmConfig } = useQuery({
        queryKey: ['llmConfig'],
        queryFn: api.getLlmConfig,
    });

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    useEffect(() => {
        if (llmConfig?.current_model) {
            setSelectedModel(llmConfig.current_model);
        }
    }, [llmConfig]);

    const gpuInfo = gpuStatus && !gpuStatus.error
        ? `GPU: ${(gpuStatus.memory_used_mb / 1024).toFixed(1)}/${(gpuStatus.memory_total_mb / 1024).toFixed(1)}GB`
        : 'GPU: N/A';

    return (
        <div className="glass flex flex-col h-[600px]">
            {/* Model Bar */}
            <div className="flex items-center justify-between p-4 border-b border-gray-700">
                <div className="flex items-center gap-3">
                    <Cpu className="w-5 h-5 text-purple-400" />
                    <span className="text-gray-400">Model:</span>
                    <select
                        className="bg-gray-800 border border-gray-600 rounded px-3 py-1 text-sm max-w-[200px]"
                        value={selectedModel}
                        onChange={(e) => {
                            const nextModel = e.target.value;
                            setSelectedModel(nextModel);
                            switchModelMutation.mutate(nextModel);
                        }}
                    >
                        {llmConfig?.models?.map((model: any) => (
                            <option key={model.id} value={model.id}>
                                {model.name} {model.recommended && '(Recommended)'}
                            </option>
                        ))}
                        {!llmConfig && <option>Loading...</option>}
                    </select>
                </div>
                <span className="text-sm text-gray-500">{gpuInfo}</span>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg, index) => (
                    <div
                        key={index}
                        className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}
                    >
                        {msg.role === 'assistant' && (
                            <div className="w-8 h-8 rounded-full bg-purple-600/30 flex items-center justify-center">
                                <Bot className="w-4 h-4 text-purple-400" />
                            </div>
                        )}
                        <div
                            className={`max-w-[70%] p-3 rounded-lg ${msg.role === 'user'
                                ? 'bg-blue-600/30 text-white'
                                : 'bg-gray-700/50 text-gray-200'
                                }`}
                        >
                            <p className="whitespace-pre-wrap">{msg.content}</p>
                            <span className="text-xs text-gray-500 mt-1 block">
                                {msg.timestamp.toLocaleTimeString()}
                            </span>
                        </div>
                        {msg.role === 'user' && (
                            <div className="w-8 h-8 rounded-full bg-blue-600/30 flex items-center justify-center">
                                <User className="w-4 h-4 text-blue-400" />
                            </div>
                        )}
                    </div>
                ))}
                {sendMessageMutation.isPending && (
                    <div className="flex gap-3">
                        <div className="w-8 h-8 rounded-full bg-purple-600/30 flex items-center justify-center">
                            <Bot className="w-4 h-4 text-purple-400" />
                        </div>
                        <div className="bg-gray-700/50 p-3 rounded-lg">
                            <div className="flex gap-1">
                                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t border-gray-700">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Chiedi informazioni sui database, alert, o stato del sistema..."
                        className="flex-1 bg-gray-800 border border-gray-600 rounded-lg px-4 py-3 focus:outline-none focus:border-purple-500"
                    />
                    <button
                        onClick={handleSend}
                        disabled={sendMessageMutation.isPending || !input.trim()}
                        className="btn-primary px-4"
                    >
                        <Send className="w-5 h-5" />
                    </button>
                </div>
            </div>
        </div>
    );
}
