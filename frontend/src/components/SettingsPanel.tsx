import type { MergeSettings, OutputPreset, PersonSettings } from "../types/index.ts";
import { OUTPUT_PRESETS, DEFAULT_MERGE_SETTINGS, DEFAULT_PERSON1_SETTINGS, DEFAULT_PERSON2_SETTINGS } from "../types/index.ts";

interface SettingsPanelProps {
  settings: MergeSettings;
  onChange: (settings: MergeSettings) => void;
  disabled?: boolean;
}

function PersonControls({
  label,
  person,
  defaultPerson,
  onChange,
}: {
  label: string;
  person: PersonSettings;
  defaultPerson: PersonSettings;
  onChange: (p: PersonSettings) => void;
}) {
  return (
    <fieldset className="border border-gray-200 rounded-lg p-3 space-y-2">
      <legend className="text-xs font-semibold text-gray-700 px-1">
        <span className="inline-flex items-center gap-2">
          {label}
          <button
            onClick={() => onChange(defaultPerson)}
            className="text-[10px] text-gray-400 hover:text-blue-600 transition-colors"
          >
            リセット
          </button>
        </span>
      </legend>

      <div>
        <label className="block text-xs text-gray-500">位置</label>
        <input
          type="range"
          min={-50}
          max={150}
          value={Math.round(person.x * 100)}
          onChange={(e) => onChange({ ...person, x: Number(e.target.value) / 100 })}
          className="w-full"
        />
      </div>

      <div>
        <label className="block text-xs text-gray-500">
          スケール ({Math.round(person.scale * 100)}%)
        </label>
        <input
          type="range"
          min={50}
          max={200}
          value={Math.round(person.scale * 100)}
          onChange={(e) => onChange({ ...person, scale: Number(e.target.value) / 100 })}
          className="w-full"
        />
      </div>

      <div>
        <label className="block text-xs text-gray-500">回転 ({person.rotation}°)</label>
        <input
          type="range"
          min={-45}
          max={45}
          step={1}
          value={person.rotation}
          onChange={(e) => onChange({ ...person, rotation: Number(e.target.value) })}
          className="w-full"
        />
      </div>

      <div className="flex gap-2">
        <button
          onClick={() => onChange({ ...person, flipH: !person.flipH })}
          className={`flex-1 text-xs border rounded px-2 py-1 transition-colors ${
            person.flipH
              ? "bg-blue-100 border-blue-400 text-blue-700"
              : "border-gray-300 text-gray-600 hover:bg-gray-50"
          }`}
        >
          ↔ 左右反転
        </button>
        <button
          onClick={() => onChange({ ...person, flipV: !person.flipV })}
          className={`flex-1 text-xs border rounded px-2 py-1 transition-colors ${
            person.flipV
              ? "bg-blue-100 border-blue-400 text-blue-700"
              : "border-gray-300 text-gray-600 hover:bg-gray-50"
          }`}
        >
          ↕ 上下反転
        </button>
      </div>
    </fieldset>
  );
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
    <div className={`space-y-3 ${disabled ? "opacity-50 pointer-events-none" : ""}`}>
      <div className="flex items-center justify-between border-b pb-2">
        <h3 className="text-sm font-semibold text-gray-800">合成設定</h3>
        <button
          onClick={() => onChange(DEFAULT_MERGE_SETTINGS)}
          className="text-xs text-gray-500 hover:text-blue-600 transition-colors"
        >
          設定リセット
        </button>
      </div>

      {/* Person 1 & 2 Controls */}
      <PersonControls
        label="人物1"
        person={settings.person1}
        defaultPerson={DEFAULT_PERSON1_SETTINGS}
        onChange={(p) => onChange({ ...settings, person1: p })}
      />
      <PersonControls
        label="人物2"
        person={settings.person2}
        defaultPerson={DEFAULT_PERSON2_SETTINGS}
        onChange={(p) => onChange({ ...settings, person2: p })}
      />

      {/* General Settings */}
      <fieldset className="border border-gray-200 rounded-lg p-3 space-y-2">
        <legend className="text-xs font-semibold text-gray-700 px-1">共通設定</legend>

        {/* Background Color */}
        <div>
          <label className="block text-xs text-gray-500">背景色</label>
          <div className="flex items-center gap-2 mt-0.5">
            <input
              type="color"
              value={settings.backgroundColor}
              onChange={(e) => onChange({ ...settings, backgroundColor: e.target.value })}
              className="w-7 h-7 rounded border border-gray-300 cursor-pointer"
            />
            <span className="text-xs text-gray-400">{settings.backgroundColor}</span>
          </div>
        </div>

        {/* Output Size Preset */}
        <div>
          <label className="block text-xs text-gray-500">出力サイズ</label>
          <select
            value={settings.outputSize.preset}
            onChange={(e) => handlePresetChange(e.target.value as OutputPreset)}
            className="w-full text-xs border border-gray-300 rounded px-2 py-1.5 bg-white mt-0.5"
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
                className="w-20 text-xs border border-gray-300 rounded px-2 py-1"
                placeholder="幅"
              />
              <span className="text-gray-400 self-center text-xs">x</span>
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
                className="w-20 text-xs border border-gray-300 rounded px-2 py-1"
                placeholder="高さ"
              />
            </div>
          )}
        </div>

        {/* Shadow */}
        <div>
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
            <label htmlFor="shadow-toggle" className="text-xs text-gray-500">
              影
            </label>
          </div>
          {settings.shadow.enabled && (
            <div className="mt-1">
              <label className="block text-xs text-gray-400">
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
            </div>
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
          <label htmlFor="color-correction-toggle" className="text-xs text-gray-500">
            色調補正
          </label>
        </div>

        {/* Layer Order */}
        <div>
          <label className="block text-xs text-gray-500">レイヤー順序</label>
          <button
            onClick={() =>
              onChange({
                ...settings,
                layerOrder: settings.layerOrder === "person1_back" ? "person2_back" : "person1_back",
              })
            }
            className="w-full text-xs border border-gray-300 rounded px-2 py-1.5 bg-white hover:bg-gray-50 transition-colors text-left mt-0.5"
          >
            {settings.layerOrder === "person1_back"
              ? "前面: 人物2 ／ 背面: 人物1"
              : "前面: 人物1 ／ 背面: 人物2"}
            <span className="float-right text-gray-400">切替</span>
          </button>
        </div>
      </fieldset>
    </div>
  );
}
