import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { DownloadButton } from "../../src/components/DownloadButton.tsx";

describe("DownloadButton", () => {
  it("renders download button", () => {
    render(
      <DownloadButton
        phase="PREVIEW"
        onDownload={vi.fn()}
        onReset={vi.fn()}
        isMerging={false}
      />
    );
    expect(screen.getByText("ダウンロード")).toBeInTheDocument();
  });

  it("disables download in IDLE phase", () => {
    render(
      <DownloadButton
        phase="IDLE"
        onDownload={vi.fn()}
        onReset={vi.fn()}
        isMerging={false}
      />
    );
    const button = screen.getByText("ダウンロード");
    expect(button.closest("button")).toBeDisabled();
  });

  it("enables download in PREVIEW phase", () => {
    render(
      <DownloadButton
        phase="PREVIEW"
        onDownload={vi.fn()}
        onReset={vi.fn()}
        isMerging={false}
      />
    );
    const button = screen.getByText("ダウンロード");
    expect(button.closest("button")).not.toBeDisabled();
  });

  it("shows spinner during merging", () => {
    const { container } = render(
      <DownloadButton
        phase="PREVIEW"
        onDownload={vi.fn()}
        onReset={vi.fn()}
        isMerging={true}
      />
    );
    expect(screen.getByText("合成中...")).toBeInTheDocument();
    const spinner = container.querySelector("[class*='animate-spin']");
    expect(spinner).not.toBeNull();
  });

  it("calls onDownload when clicked", () => {
    const onDownload = vi.fn();
    render(
      <DownloadButton
        phase="PREVIEW"
        onDownload={onDownload}
        onReset={vi.fn()}
        isMerging={false}
      />
    );
    fireEvent.click(screen.getByText("ダウンロード"));
    expect(onDownload).toHaveBeenCalledTimes(1);
  });

  it("shows 'もう1枚作る' button in COMPLETE phase", () => {
    render(
      <DownloadButton
        phase="COMPLETE"
        onDownload={vi.fn()}
        onReset={vi.fn()}
        isMerging={false}
      />
    );
    expect(screen.getByText("もう1枚作る")).toBeInTheDocument();
  });

  it("always shows reset button", () => {
    render(
      <DownloadButton
        phase="IDLE"
        onDownload={vi.fn()}
        onReset={vi.fn()}
        isMerging={false}
      />
    );
    expect(screen.getByText("リセット")).toBeInTheDocument();
  });

  it("calls onReset when reset clicked", () => {
    const onReset = vi.fn();
    render(
      <DownloadButton
        phase="PREVIEW"
        onDownload={vi.fn()}
        onReset={onReset}
        isMerging={false}
      />
    );
    fireEvent.click(screen.getByText("リセット"));
    expect(onReset).toHaveBeenCalledTimes(1);
  });
});
