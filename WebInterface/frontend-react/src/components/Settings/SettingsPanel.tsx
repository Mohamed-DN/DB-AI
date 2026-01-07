import { useState, useEffect } from 'react';
import { Save, RefreshCw } from 'lucide-react';

const AGENT_SETTINGS = [
    { id: 'scout', name: 'Scout Agent', default: 300 },
    { id: 'collector', name: 'Collector', default: 60 },
    { id: 'watcher', name: 'Watcher', default: 30 },
    { id: 'criticalalert', name: 'Critical Alert', default: 60 },
    { id: 'forensicanalyzer', name: 'Forensic AI', default: 300 },
    { id: 'checkmk_bridge', name: 'CheckMK Bridge', default: 120 },
];

export default function SettingsPanel() {
    const [settings, setSettings] = useState<Record<string, number>>({});
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        loadSettings();
    }, []);

    const loadSettings = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/config');
            const config = await res.json();
            const newSettings: Record<string, number> = {};
            AGENT_SETTINGS.forEach((agent) => {
                newSettings[agent.id] = config[`${agent.id}_interval`] || agent.default;
            });
            setSettings(newSettings);
        } catch (e) {
            console.error('Failed to load settings:', e);
        }
    };

    const saveSettings = async () => {
        setSaving(true);
        try {
            const config: Record<string, number> = {};
            Object.keys(settings).forEach((key) => {
                config[`${key}_interval`] = settings[key];
            });
            await fetch('http://localhost:8000/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config),
            });
            alert('Settings saved!');
        } catch (e) {
            alert('Failed to save settings');
        }
        setSaving(false);
    };

    return (
        <div className="glass p-6">
            <h3 className="text-lg font-semibold mb-6">Agent Intervals (seconds)</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {AGENT_SETTINGS.map((agent) => (
                    <div key={agent.id}>
                        <label className="block text-sm text-gray-400 mb-2">{agent.name}</label>
                        <input
                            type="number"
                            value={settings[agent.id] || agent.default}
                            onChange={(e) =>
                                setSettings((prev) => ({
                                    ...prev,
                                    [agent.id]: parseInt(e.target.value) || agent.default,
                                }))
                            }
                            className="w-full bg-gray-800 border border-gray-600 rounded px-4 py-2 focus:outline-none focus:border-purple-500"
                        />
                    </div>
                ))}
            </div>

            <div className="flex gap-4 mt-8">
                <button onClick={saveSettings} disabled={saving} className="btn-primary">
                    <Save className="w-4 h-4" />
                    {saving ? 'Saving...' : 'Save Settings'}
                </button>
                <button onClick={loadSettings} className="btn-secondary">
                    <RefreshCw className="w-4 h-4" />
                    Reset
                </button>
            </div>
        </div>
    );
}
