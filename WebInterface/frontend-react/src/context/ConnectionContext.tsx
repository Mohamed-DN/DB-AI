import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import ConnectionModal from '../components/common/ConnectionModal';
import { connectDatabase } from '../services/api';

interface ConnectionState {
    isOpen: boolean;
    dbName: string;
    mode: 'sql' | 'bash' | 'sysdba';
    status: 'connecting' | 'success' | 'error';
    message?: string;
}

interface ConnectionContextType {
    connect: (dbName: string, mode: 'sql' | 'bash' | 'sysdba') => void;
}

const ConnectionContext = createContext<ConnectionContextType | null>(null);

export function ConnectionProvider({ children }: { children: ReactNode }) {
    const [state, setState] = useState<ConnectionState>({
        isOpen: false,
        dbName: '',
        mode: 'sql',
        status: 'connecting',
        message: ''
    });

    const connect = useCallback(async (dbName: string, mode: 'sql' | 'bash' | 'sysdba') => {
        // Open modal in connecting state
        setState({
            isOpen: true,
            dbName,
            mode,
            status: 'connecting',
            message: ''
        });

        try {
            // Call the API
            const result = await connectDatabase(dbName, mode);

            // Success
            setState(prev => ({
                ...prev,
                status: 'success',
                message: result.status || 'Connection established!'
            }));

            // Auto-close after 2 seconds on success
            setTimeout(() => {
                setState(prev => ({ ...prev, isOpen: false }));
            }, 2000);
        } catch (error: any) {
            // Error
            setState(prev => ({
                ...prev,
                status: 'error',
                message: error.response?.data?.detail || error.message || 'Connection failed'
            }));
        }
    }, []);

    const handleClose = useCallback(() => {
        setState(prev => ({ ...prev, isOpen: false }));
    }, []);

    return (
        <ConnectionContext.Provider value={{ connect }}>
            {children}
            <ConnectionModal
                isOpen={state.isOpen}
                onClose={handleClose}
                dbName={state.dbName}
                mode={state.mode}
                status={state.status}
                message={state.message}
            />
        </ConnectionContext.Provider>
    );
}

export function useConnection() {
    const context = useContext(ConnectionContext);
    if (!context) {
        throw new Error('useConnection must be used within a ConnectionProvider');
    }
    return context;
}
