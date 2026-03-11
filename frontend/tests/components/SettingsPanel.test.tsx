import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { SettingsPanel } from "../../src/components/SettingsPanel.tsx";
import { DEFAULT_MERGE_SETTINGS } from "../../src/types/index.ts";
import type { MergeSettings } from "../../src/types/index.ts";

describe("SettingsPanel", () => {
  it("renders all settings sections", () => {
    render(
      <SettingsPanel
        settings={DEFAULT_MERGE_SETTINGS}
        onChange={vi.fn()}
      />
    );
    expect(screen.getByText("合成設定")).toBeInTheDocument();
    expect(screen.getByText("背景色")).toBeInTheDocument();
    expect(screen.getByText("出力サイズ")).toBeInTheDocument();
    expect(screen.getByText("影")).toBeInTheDocument();
    expect(screen.getByText("色調補正")).toBeInTheDocument();
  });

  it("calls onChange when background color changes", () => {
    const onChange = vi.fn();
    render(
      <SettingsPanel
        settings={DEFAULT_MERGE_SETTINGS}
        onChange={onChange}
      />
    );

    const colorInput = document.querySelector('input[type="color"]') as HTMLInputElement;
    fireEvent.change(colorInput, { target: { value: "#FF0000" } });

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ backgroundColor: "#ff0000" })
    );
  });

  it("calls onChange when output preset changes", () => {
    const onChange = vi.fn();
    render(
      <SettingsPanel
        settings={DEFAULT_MERGE_SETTINGS}
        onChange={onChange}
      />
    );

    const select = screen.getByRole("combobox");
    fireEvent.change(select, { target: { value: "landscape" } });

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        outputSize: expect.objectContaining({
          width: 1920,
          height: 1080,
          preset: "landscape",
        }),
      })
    );
  });

  it("applies disabled styling when disabled", () => {
    const { container } = render(
      <SettingsPanel
        settings={DEFAULT_MERGE_SETTINGS}
        onChange={vi.fn()}
        disabled
      />
    );

    const panel = container.querySelector("[class*='opacity-50']");
    expect(panel).not.toBeNull();
  });

  it("toggles shadow enabled", () => {
    const onChange = vi.fn();
    render(
      <SettingsPanel
        settings={DEFAULT_MERGE_SETTINGS}
        onChange={onChange}
      />
    );

    const shadowToggle = screen.getByLabelText("影");
    fireEvent.click(shadowToggle);

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        shadow: expect.objectContaining({ enabled: false }),
      })
    );
  });

  it("toggles color correction", () => {
    const onChange = vi.fn();
    render(
      <SettingsPanel
        settings={DEFAULT_MERGE_SETTINGS}
        onChange={onChange}
      />
    );

    const colorToggle = screen.getByLabelText("色調補正");
    fireEvent.click(colorToggle);

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ colorCorrection: false })
    );
  });

  it("calls onChange when person1 position slider changes", () => {
    const onChange = vi.fn();
    render(
      <SettingsPanel
        settings={DEFAULT_MERGE_SETTINGS}
        onChange={onChange}
      />
    );

    // person1 position is the first range input
    const sliders = document.querySelectorAll('input[type="range"]');
    const person1PositionSlider = sliders[0] as HTMLInputElement;
    fireEvent.change(person1PositionSlider, { target: { value: "50" } });

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        person1: expect.objectContaining({ x: 0.5 }),
      })
    );
  });

  it("calls onChange when person1 scale slider changes", () => {
    const onChange = vi.fn();
    render(
      <SettingsPanel
        settings={DEFAULT_MERGE_SETTINGS}
        onChange={onChange}
      />
    );

    const sliders = document.querySelectorAll('input[type="range"]');
    const person1ScaleSlider = sliders[1] as HTMLInputElement;
    fireEvent.change(person1ScaleSlider, { target: { value: "150" } });

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        person1: expect.objectContaining({ scale: 1.5 }),
      })
    );
  });

  it("calls onChange when person2 position slider changes", () => {
    const onChange = vi.fn();
    render(
      <SettingsPanel
        settings={DEFAULT_MERGE_SETTINGS}
        onChange={onChange}
      />
    );

    const sliders = document.querySelectorAll('input[type="range"]');
    const person2PositionSlider = sliders[3] as HTMLInputElement;
    fireEvent.change(person2PositionSlider, { target: { value: "80" } });

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        person2: expect.objectContaining({ x: 0.8 }),
      })
    );
  });

  it("calls onChange when person2 scale slider changes", () => {
    const onChange = vi.fn();
    render(
      <SettingsPanel
        settings={DEFAULT_MERGE_SETTINGS}
        onChange={onChange}
      />
    );

    const sliders = document.querySelectorAll('input[type="range"]');
    const person2ScaleSlider = sliders[4] as HTMLInputElement;
    fireEvent.change(person2ScaleSlider, { target: { value: "75" } });

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        person2: expect.objectContaining({ scale: 0.75 }),
      })
    );
  });

  it("shows shadow intensity slider when shadow is enabled", () => {
    const onChange = vi.fn();
    render(
      <SettingsPanel
        settings={DEFAULT_MERGE_SETTINGS}
        onChange={onChange}
      />
    );

    // Shadow is enabled by default, so intensity slider should be visible
    expect(screen.getByText(/強度/)).toBeInTheDocument();
  });

  it("hides shadow intensity slider when shadow is disabled", () => {
    const settingsWithShadowOff: MergeSettings = {
      ...DEFAULT_MERGE_SETTINGS,
      shadow: { enabled: false, intensity: 0.5 },
    };
    render(
      <SettingsPanel
        settings={settingsWithShadowOff}
        onChange={vi.fn()}
      />
    );

    expect(screen.queryByText(/強度/)).toBeNull();
  });

  it("calls onChange when shadow intensity slider changes", () => {
    const onChange = vi.fn();
    render(
      <SettingsPanel
        settings={DEFAULT_MERGE_SETTINGS}
        onChange={onChange}
      />
    );

    // Shadow intensity is the last range slider when shadow enabled
    const sliders = document.querySelectorAll('input[type="range"]');
    const shadowIntensitySlider = sliders[sliders.length - 1] as HTMLInputElement;
    fireEvent.change(shadowIntensitySlider, { target: { value: "80" } });

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        shadow: expect.objectContaining({ intensity: 0.8 }),
      })
    );
  });

  it("selects portrait preset correctly", () => {
    const onChange = vi.fn();
    render(
      <SettingsPanel
        settings={DEFAULT_MERGE_SETTINGS}
        onChange={onChange}
      />
    );

    const select = screen.getByRole("combobox");
    fireEvent.change(select, { target: { value: "portrait" } });

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        outputSize: expect.objectContaining({
          width: 1080,
          height: 1920,
          preset: "portrait",
        }),
      })
    );
  });

  it("shows custom width/height inputs when custom preset is selected", () => {
    const customSettings: MergeSettings = {
      ...DEFAULT_MERGE_SETTINGS,
      outputSize: { width: 800, height: 600, preset: "custom" },
    };
    render(
      <SettingsPanel
        settings={customSettings}
        onChange={vi.fn()}
      />
    );

    const numberInputs = document.querySelectorAll('input[type="number"]');
    expect(numberInputs.length).toBe(2);
  });

  it("does not show custom inputs for non-custom presets", () => {
    render(
      <SettingsPanel
        settings={DEFAULT_MERGE_SETTINGS}
        onChange={vi.fn()}
      />
    );

    const numberInputs = document.querySelectorAll('input[type="number"]');
    expect(numberInputs.length).toBe(0);
  });

  it("calls onChange when custom width changes", () => {
    const onChange = vi.fn();
    const customSettings: MergeSettings = {
      ...DEFAULT_MERGE_SETTINGS,
      outputSize: { width: 800, height: 600, preset: "custom" },
    };
    render(
      <SettingsPanel
        settings={customSettings}
        onChange={onChange}
      />
    );

    const numberInputs = document.querySelectorAll('input[type="number"]');
    fireEvent.change(numberInputs[0], { target: { value: "1920" } });

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        outputSize: expect.objectContaining({ width: 1920 }),
      })
    );
  });

  it("calls onChange when custom height changes", () => {
    const onChange = vi.fn();
    const customSettings: MergeSettings = {
      ...DEFAULT_MERGE_SETTINGS,
      outputSize: { width: 800, height: 600, preset: "custom" },
    };
    render(
      <SettingsPanel
        settings={customSettings}
        onChange={onChange}
      />
    );

    const numberInputs = document.querySelectorAll('input[type="number"]');
    fireEvent.change(numberInputs[1], { target: { value: "1080" } });

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        outputSize: expect.objectContaining({ height: 1080 }),
      })
    );
  });

  it("does not apply disabled class when disabled is false", () => {
    const { container } = render(
      <SettingsPanel
        settings={DEFAULT_MERGE_SETTINGS}
        onChange={vi.fn()}
      />
    );

    const panel = container.querySelector("[class*='pointer-events-none']");
    expect(panel).toBeNull();
  });
});
