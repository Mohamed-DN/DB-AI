import { useState } from 'react';
import { Mail, Trash2, Inbox } from 'lucide-react';
import { useEmails } from '../../hooks/useDatabases';

export default function MailboxPanel() {
    const { data: emails, isLoading, refetch } = useEmails();
    const [selectedEmail, setSelectedEmail] = useState<string | null>(null);
    const [emailContent, setEmailContent] = useState<string>('');

    const viewEmail = async (filename: string) => {
        setSelectedEmail(filename);
        try {
            const res = await fetch(`/api/emails/content?filename=${filename}`);
            const data = await res.json();
            setEmailContent(data.content || 'No content');
        } catch (e) {
            setEmailContent('Error loading email');
        }
    };

    const deleteEmail = async (filename: string) => {
        try {
            await fetch(`/api/emails/${filename}`, { method: 'DELETE' });
            refetch();
            setSelectedEmail(null);
            setEmailContent('');
        } catch (e) {
            console.error('Failed to delete email:', e);
        }
    };

    if (isLoading) {
        return <div className="glass p-8 text-center text-gray-500">Loading emails...</div>;
    }

    return (
        <div className="flex gap-4 h-[600px]">
            {/* Email List */}
            <div className="w-1/3 glass overflow-y-auto">
                {emails && emails.length > 0 ? (
                    emails.map((email: string) => (
                        <div
                            key={email}
                            className={`p-4 border-b border-gray-700 cursor-pointer hover:bg-gray-700/30 flex justify-between items-center ${selectedEmail === email ? 'bg-gray-700/50' : ''
                                }`}
                        >
                            <button
                                onClick={() => viewEmail(email)}
                                className="flex items-center gap-2 text-left flex-1"
                            >
                                <Mail className="w-4 h-4 text-blue-400" />
                                <span className="text-sm truncate">
                                    {email.replace('alert_', '').replace('.html', '').replace(/_/g, ' ')}
                                </span>
                            </button>
                            <button
                                onClick={() => deleteEmail(email)}
                                className="text-red-400 hover:text-red-300 p-1"
                            >
                                <Trash2 className="w-4 h-4" />
                            </button>
                        </div>
                    ))
                ) : (
                    <div className="p-8 text-center text-gray-500">
                        <Inbox className="w-12 h-12 mx-auto mb-2 opacity-30" />
                        <p>No emails</p>
                    </div>
                )}
            </div>

            {/* Email Preview */}
            <div className="flex-1 glass">
                {emailContent ? (
                    <iframe
                        srcDoc={emailContent}
                        className="w-full h-full border-0 bg-black"
                        title="Email Preview"
                    />
                ) : (
                    <div className="w-full h-full flex items-center justify-center text-gray-500">
                        Select an email to preview
                    </div>
                )}
            </div>
        </div>
    );
}
