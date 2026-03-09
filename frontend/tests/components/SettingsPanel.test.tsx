import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { SettingsPanel } from "../../src/components/SettingsPanel.tsx";
import { DEFAULT_MERGE_SETTINGS } from "../../src/types/index.ts";

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
          width: 1280,
          height: 720,
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
});
