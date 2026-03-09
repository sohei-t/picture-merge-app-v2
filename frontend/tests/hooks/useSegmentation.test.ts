import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useSegmentation } from "../../src/hooks/useSegmentation.ts";
import * as api from "../../src/api/client.ts";

vi.mock("../../src/api/client.ts", () => ({
  segmentImage: vi.fn(),
}));

const mockSegmentResponse = {
  id: "seg-1",
  segmented_image: "data:image/png;base64,abc",
  bbox: { x: 10, y: 20, width: 100, height: 200 },
  foot_y: 210,
  original_size: { width: 640, height: 480 },
  processing_time_ms: 1200,
};

describe("useSegmentation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("initializes with null values", () => {
    const { result } = renderHook(() => useSegmentation());
    expect(result.current.person1).toBeNull();
    expect(result.current.person2).toBeNull();
    expect(result.current.isProcessing).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("segments both images successfully", async () => {
    vi.mocked(api.segmentImage).mockResolvedValue(mockSegmentResponse);

    const { result } = renderHook(() => useSegmentation());

    const file1 = new File(["data1"], "img1.jpg", { type: "image/jpeg" });
    const file2 = new File(["data2"], "img2.jpg", { type: "image/jpeg" });

    await act(async () => {
      await result.current.segmentBoth(file1, file2);
    });

    expect(result.current.person1).not.toBeNull();
    expect(result.current.person1?.id).toBe("seg-1");
    expect(result.current.person1?.footY).toBe(210);
    expect(result.current.person2).not.toBeNull();
    expect(result.current.isProcessing).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("sets error on segmentation failure", async () => {
    const mockError = {
      type: "segmentation" as const,
      message: "Segmentation failed",
      retryable: false,
    };
    vi.mocked(api.segmentImage).mockRejectedValue(mockError);

    const { result } = renderHook(() => useSegmentation());

    const file1 = new File(["data1"], "img1.jpg", { type: "image/jpeg" });
    const file2 = new File(["data2"], "img2.jpg", { type: "image/jpeg" });

    await act(async () => {
      await result.current.segmentBoth(file1, file2);
    });

    expect(result.current.error).toEqual(mockError);
    expect(result.current.isProcessing).toBe(false);
  });

  it("resets all state", async () => {
    vi.mocked(api.segmentImage).mockResolvedValue(mockSegmentResponse);

    const { result } = renderHook(() => useSegmentation());

    const file1 = new File(["data1"], "img1.jpg", { type: "image/jpeg" });
    const file2 = new File(["data2"], "img2.jpg", { type: "image/jpeg" });

    await act(async () => {
      await result.current.segmentBoth(file1, file2);
    });

    expect(result.current.person1).not.toBeNull();

    act(() => {
      result.current.reset();
    });

    expect(result.current.person1).toBeNull();
    expect(result.current.person2).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.isProcessing).toBe(false);
  });
});
