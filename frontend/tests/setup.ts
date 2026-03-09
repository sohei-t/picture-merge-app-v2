import "@testing-library/jest-dom/vitest";

// Mock URL.createObjectURL / revokeObjectURL
if (typeof globalThis.URL.createObjectURL === "undefined") {
  globalThis.URL.createObjectURL = vi.fn(() => "blob:mock-url");
}
if (typeof globalThis.URL.revokeObjectURL === "undefined") {
  globalThis.URL.revokeObjectURL = vi.fn();
}

// Mock HTMLCanvasElement.getContext
HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
  drawImage: vi.fn(),
  fillRect: vi.fn(),
  fillText: vi.fn(),
  fillStyle: "",
  font: "",
  textAlign: "",
})) as unknown as typeof HTMLCanvasElement.prototype.getContext;

// Mock Image
class MockImage {
  onload: (() => void) | null = null;
  onerror: (() => void) | null = null;
  private _src = "";

  get src() {
    return this._src;
  }
  set src(value: string) {
    this._src = value;
    if (this.onload) {
      setTimeout(() => this.onload?.(), 0);
    }
  }

  width = 512;
  height = 512;
}

globalThis.Image = MockImage as unknown as typeof Image;
