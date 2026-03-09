import { describe, it, expect, vi } from "vitest";
import { render, fireEvent } from "@testing-library/react";
import { PreviewCanvas } from "../../src/components/PreviewCanvas.tsx";

describe("PreviewCanvas", () => {
  it("renders canvas element", () => {
    const { container } = render(
      <PreviewCanvas previewImage={null} isLoading={false} />
    );
    const canvas = container.querySelector("canvas");
    expect(canvas).not.toBeNull();
  });

  it("shows loading spinner when isLoading", () => {
    const { container } = render(
      <PreviewCanvas previewImage={null} isLoading={true} />
    );
    const spinner = container.querySelector("[class*='animate-spin']");
    expect(spinner).not.toBeNull();
  });

  it("does not show loading spinner when not loading", () => {
    const { container } = render(
      <PreviewCanvas previewImage={null} isLoading={false} />
    );
    const spinner = container.querySelector("[class*='animate-spin']");
    expect(spinner).toBeNull();
  });

  it("sets cursor to grab when drag handlers provided", () => {
    const { container } = render(
      <PreviewCanvas
        previewImage={null}
        isLoading={false}
        onMouseDown={vi.fn()}
        onMouseMove={vi.fn()}
        onMouseUp={vi.fn()}
      />
    );
    const canvas = container.querySelector("canvas");
    expect(canvas?.style.cursor).toBe("grab");
  });

  it("sets cursor to default when no drag handlers", () => {
    const { container } = render(
      <PreviewCanvas previewImage={null} isLoading={false} />
    );
    const canvas = container.querySelector("canvas");
    expect(canvas?.style.cursor).toBe("default");
  });

  it("calls onMouseDown when canvas is clicked", () => {
    const onMouseDown = vi.fn();
    const { container } = render(
      <PreviewCanvas
        previewImage={null}
        isLoading={false}
        onMouseDown={onMouseDown}
      />
    );
    const canvas = container.querySelector("canvas") as HTMLCanvasElement;
    fireEvent.mouseDown(canvas);
    expect(onMouseDown).toHaveBeenCalledTimes(1);
  });

  it("calls onMouseMove when mouse moves over canvas", () => {
    const onMouseMove = vi.fn();
    const { container } = render(
      <PreviewCanvas
        previewImage={null}
        isLoading={false}
        onMouseMove={onMouseMove}
      />
    );
    const canvas = container.querySelector("canvas") as HTMLCanvasElement;
    fireEvent.mouseMove(canvas);
    expect(onMouseMove).toHaveBeenCalledTimes(1);
  });

  it("calls onMouseUp when mouse is released on canvas", () => {
    const onMouseUp = vi.fn();
    const { container } = render(
      <PreviewCanvas
        previewImage={null}
        isLoading={false}
        onMouseUp={onMouseUp}
      />
    );
    const canvas = container.querySelector("canvas") as HTMLCanvasElement;
    fireEvent.mouseUp(canvas);
    expect(onMouseUp).toHaveBeenCalledTimes(1);
  });

  it("calls onMouseUp when mouse leaves canvas", () => {
    const onMouseUp = vi.fn();
    const { container } = render(
      <PreviewCanvas
        previewImage={null}
        isLoading={false}
        onMouseUp={onMouseUp}
      />
    );
    const canvas = container.querySelector("canvas") as HTMLCanvasElement;
    fireEvent.mouseLeave(canvas);
    expect(onMouseUp).toHaveBeenCalledTimes(1);
  });

  it("draws placeholder text when no preview image", () => {
    const { container } = render(
      <PreviewCanvas previewImage={null} isLoading={false} />
    );
    const canvas = container.querySelector("canvas") as HTMLCanvasElement;
    // getContext is mocked in setup.ts, verify canvas exists
    expect(canvas).toBeTruthy();
    // The mocked getContext should have been called
    expect(HTMLCanvasElement.prototype.getContext).toHaveBeenCalledWith("2d");
  });

  it("renders canvas with previewImage set", () => {
    const { container } = render(
      <PreviewCanvas
        previewImage="data:image/png;base64,abc"
        isLoading={false}
      />
    );
    const canvas = container.querySelector("canvas") as HTMLCanvasElement;
    expect(canvas).toBeTruthy();
  });

  it("does not call mouse handlers when not provided", () => {
    const { container } = render(
      <PreviewCanvas previewImage={null} isLoading={false} />
    );
    const canvas = container.querySelector("canvas") as HTMLCanvasElement;
    // Should not throw
    fireEvent.mouseDown(canvas);
    fireEvent.mouseMove(canvas);
    fireEvent.mouseUp(canvas);
    fireEvent.mouseLeave(canvas);
  });
});
