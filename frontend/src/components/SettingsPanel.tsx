import type { MergeSettings, OutputPreset } from "../types/index.ts";
import { OUTPUT_PRESETS } from "../types/index.ts";

interface SettingsPanelProps {
  settings: MergeSettings;
  onChange: (settings: MergeSettings) => void;
  disabled?: boolean;
}

export function SettingsPanel({ settings, onChange, disabled = false }: SettingsPanelProps) {
  const handlePresetChange = (preset: OutputPreset) => {
    const presetData = OUTPUT_PRESETS[preset];
    onChange({
      ...settings,
      outputSize: {
        width: presetData.width,
        height: presetData.height,
        preset,
      },
    });
  };

  return (
    <div className={`space-y-4 ${disabled ? "opacity-50 pointer-events-none" : ""}`}>
      <h3 className="text-sm font-semibold text-gray-800 border-b pb-2">合成設定</h3>

      {/* Background Color */}
      <div className="space-y-1">
        <label className="block text-xs font-medium text-gray-600">背景色</label>
        <div className="flex items-center gap-2">
          <input
            type="color"
            value={settings.backgroundColor}
            onChange={(e) => onChange({ ...settings, backgroundColor: e.target.value })}
            className="w-8 h-8 rounded border border-gray-300 cursor-pointer"
          />
          <span className="text-xs text-gray-500">{settings.backgroundColor}</span>
        </div>
      </div>

      {/* Output Size Preset */}
      <div className="space-y-1">
        <label className="block text-xs font-medium text-gray-600">出力サイズ</label>
        <select
          value={settings.outputSize.preset}
          onChange={(e) => handlePresetChange(e.target.value as OutputPreset)}
          className="w-full text-sm border border-gray-300 rounded px-2 py-1.5 bg-white"
        >
          {(Object.keys(OUTPUT_PRESETS) as OutputPreset[]).map((key) => (
            <option key={key} value={key}>
              {OUTPUT_PRESETS[key].label}
            </option>
          ))}
        </select>
        {settings.outputSize.preset === "custom" && (
          <div className="flex gap-2 mt-1">
            <input
              type="number"
              min={64}
              max={4096}
              value={settings.outputSize.width}
              onChange={(e) =>
                onChange({
                  ...settings,
                  outputSize: { ...settings.outputSize, width: Number(e.target.value) },
                })
              }
              className="w-20 text-sm border border-gray-300 rounded px-2 py-1"
              placeholder="幅"
            />
            <span className="text-gray-400 self-center">x</span>
            <input
              type="number"
              min={64}
              max={4096}
              value={settings.outputSize.height}
              onChange={(e) =>
                onChange({
                  ...settings,
                  outputSize: { ...settings.outputSize, height: Number(e.target.value) },
                })
              }
              className="w-20 text-sm border border-gray-300 rounded px-2 py-1"
              placeholder="高さ"
            />
          </div>
        )}
      </div>

      {/* Person 1 Position & Scale */}
      <div className="space-y-1">
        <label className="block text-xs font-medium text-gray-600">人物1 位置</label>
        <input
          type="range"
          min={0}
          max={100}
          value={Math.round(settings.person1.x * 100)}
          onChange={(e) =>
            onChange({
              ...settings,
              person1: { ...settings.person1, x: Number(e.target.value) / 100 },
            })
          }
          className="w-full"
        />
        <label className="block text-xs font-medium text-gray-600">人物1 スケール ({Math.round(settings.person1.scale * 100)}%)</label>
        <input
          type="range"
          min={50}
          max={200}
          value={Math.round(settings.person1.scale * 100)}
          onChange={(e) =>
            onChange({
              ...settings,
              person1: { ...settings.person1, scale: Number(e.target.value) / 100 },
            })
          }
          className="w-full"
        />
      </div>

      {/* Person 2 Position & Scale */}
      <div className="space-y-1">
        <label className="block text-xs font-medium text-gray-600">人物2 位置</label>
        <input
          type="range"
          min={0}
          max={100}
          value={Math.round(settings.person2.x * 100)}
          onChange={(e) =>
            onChange({
              ...settings,
              person2: { ...settings.person2, x: Number(e.target.value) / 100 },
            })
          }
          className="w-full"
        />
        <label className="block text-xs font-medium text-gray-600">人物2 スケール ({Math.round(settings.person2.scale * 100)}%)</label>
        <input
          type="range"
          min={50}
          max={200}
          value={Math.round(settings.person2.scale * 100)}
          onChange={(e) =>
            onChange({
              ...settings,
              person2: { ...settings.person2, scale: Number(e.target.value) / 100 },
            })
          }
          className="w-full"
        />
      </div>

      {/* Shadow */}
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="shadow-toggle"
            checked={settings.shadow.enabled}
            onChange={(e) =>
              onChange({
                ...settings,
                shadow: { ...settings.shadow, enabled: e.target.checked },
              })
            }
            className="rounded"
          />
          <label htmlFor="shadow-toggle" className="text-xs font-medium text-gray-600">
            影
          </label>
        </div>
        {settings.shadow.enabled && (
          <>
            <label className="block text-xs text-gray-500">
              強度 ({Math.round(settings.shadow.intensity * 100)}%)
            </label>
            <input
              type="range"
              min={0}
              max={100}
              value={Math.round(settings.shadow.intensity * 100)}
              onChange={(e) =>
                onChange({
                  ...settings,
                  shadow: { ...settings.shadow, intensity: Number(e.target.value) / 100 },
                })
              }
              className="w-full"
            />
          </>
        )}
      </div>

      {/* Color Correction */}
      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="color-correction-toggle"
          checked={settings.colorCorrection}
          onChange={(e) => onChange({ ...settings, colorCorrection: e.target.checked })}
          className="rounded"
        />
        <label htmlFor="color-correction-toggle" className="text-xs font-medium text-gray-600">
          色調補正
        </label>
      </div>
    </div>
  );
}
