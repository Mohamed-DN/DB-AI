import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { API_BASE } from '../services/api';

// Types
interface User {
    username: string;
    email: string | null;
    full_name: string | null;
    role: 'admin' | 'operator' | 'viewer';
    is_active: boolean;
    databases_scope: string[];
    permissions: {
        can_start_stop: boolean;
        can_execute_sql: boolean;
        can_use_llm: boolean;
        can_manage_users: boolean;
        can_delete_databases: boolean;
    };
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (username: string, password: string) => Promise<{ success: boolean; error?: string }>;
    logout: () => void;
    hasPermission: (permission: keyof User['permissions']) => boolean;
    isRole: (role: User['role']) => boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

// Token storage key
const TOKEN_KEY = 'm-dn_auth_token';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
    const [isLoading, setIsLoading] = useState(true);

    // Fetch user profile with token
    const fetchUserProfile = useCallback(async (authToken: string) => {
        try {
            const response = await fetch(`${API_BASE}/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                },
            });

            if (response.ok) {
                const userData = await response.json();
                setUser(userData);
                return true;
            } else {
                // Token invalid or expired
                localStorage.removeItem(TOKEN_KEY);
                setToken(null);
                setUser(null);
                return false;
            }
        } catch (error) {
            console.error('Failed to fetch user profile:', error);
            return false;
        }
    }, []);

    // Check token on mount
    useEffect(() => {
        const initAuth = async () => {
            if (token) {
                await fetchUserProfile(token);
            }
            setIsLoading(false);
        };
        initAuth();
    }, [token, fetchUserProfile]);

    // Login function
    const login = async (username: string, password: string): Promise<{ success: boolean; error?: string }> => {
        try {
            const response = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password }),
            });

            if (response.ok) {
                const data = await response.json();
                const newToken = data.access_token;

                // Save token
                localStorage.setItem(TOKEN_KEY, newToken);
                setToken(newToken);

                // Fetch user profile
                await fetchUserProfile(newToken);

                return { success: true };
            } else {
                const error = await response.json();
                return { success: false, error: error.detail || 'Login failed' };
            }
        } catch (error) {
            console.error('Login error:', error);
            return { success: false, error: 'Network error. Please try again.' };
        }
    };

    // Logout function
    const logout = () => {
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
        setUser(null);
    };

    // Check permission
    const hasPermission = (permission: keyof User['permissions']): boolean => {
        if (!user) return false;
        return user.permissions[permission] ?? false;
    };

    // Check role
    const isRole = (role: User['role']): boolean => {
        if (!user) return false;
        return user.role === role;
    };

    const value: AuthContextType = {
        user,
        token,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        hasPermission,
        isRole,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Hook to use auth context
export const useAuth = (): AuthContextType => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

// HOC for protected routes
export const withAuth = <P extends object>(
    WrappedComponent: React.ComponentType<P>,
    requiredPermission?: keyof User['permissions']
): React.FC<P> => {
    return (props: P) => {
        const { isAuthenticated, isLoading, hasPermission } = useAuth();

        if (isLoading) {
            return (
                <div className="flex items-center justify-center h-screen">
                    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
                </div>
            );
        }

        if (!isAuthenticated) {
            return null; // Will be handled by App.tsx redirect
        }

        if (requiredPermission && !hasPermission(requiredPermission)) {
            return (
                <div className="flex items-center justify-center h-screen">
                    <div className="text-center">
                        <h1 className="text-2xl font-bold text-red-500">Access Denied</h1>
                        <p className="text-gray-500 mt-2">You don't have permission to view this page.</p>
                    </div>
                </div>
            );
        }

        return <WrappedComponent {...props} />;
    };
};

export default AuthContext;
