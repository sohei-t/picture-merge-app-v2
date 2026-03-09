import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useMerge } from "../../src/hooks/useMerge.ts";
import * as api from "../../src/api/client.ts";
import type { MergeSettings } from "../../src/types/index.ts";
import { DEFAULT_MERGE_SETTINGS } from "../../src/types/index.ts";

vi.mock("../../src/api/client.ts", () => ({
  mergeImages: vi.fn(),
}));

const mockMergeResponse = {
  merged_image: "data:image/png;base64,merged",
  processing_time_ms: 2000,
  output_size: { width: 1024, height: 1024 },
};

describe("useMerge", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  it("initializes with null values", () => {
    const { result } = renderHook(() => useMerge());
    expect(result.current.previewImage).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.processingTimeMs).toBeNull();
  });

  it("fetchPreview debounces requests", async () => {
    vi.mocked(api.mergeImages).mockResolvedValue(mockMergeResponse);

    const { result } = renderHook(() => useMerge());
    const settings: MergeSettings = DEFAULT_MERGE_SETTINGS;

    act(() => {
      result.current.fetchPreview("id-1", "id-2", settings);
      result.current.fetchPreview("id-1", "id-2", settings);
      result.current.fetchPreview("id-1", "id-2", settings);
    });

    // Only 1 call should be made after debounce
    await act(async () => {
      vi.advanceTimersByTime(300);
      // Wait for the async fetch to complete
      await vi.runAllTimersAsync();
    });

    expect(api.mergeImages).toHaveBeenCalledTimes(1);
  });

  it("fetchFullResolution returns response directly", async () => {
    vi.useRealTimers();
    vi.mocked(api.mergeImages).mockResolvedValue(mockMergeResponse);

    const { result } = renderHook(() => useMerge());

    let response;
    await act(async () => {
      response = await result.current.fetchFullResolution(
        "id-1",
        "id-2",
        DEFAULT_MERGE_SETTINGS
      );
    });

    expect(response).toEqual(mockMergeResponse);
    expect(result.current.processingTimeMs).toBe(2000);
  });

  it("sets error on merge failure", async () => {
    vi.useRealTimers();
    const mockError = {
      type: "merge" as const,
      message: "Merge failed",
      retryable: true,
    };
    vi.mocked(api.mergeImages).mockRejectedValue(mockError);

    const { result } = renderHook(() => useMerge());

    await act(async () => {
      try {
        await result.current.fetchFullResolution("id-1", "id-2", DEFAULT_MERGE_SETTINGS);
      } catch {
        // Expected
      }
    });

    expect(result.current.error).toEqual(mockError);
  });

  it("resets all state", () => {
    const { result } = renderHook(() => useMerge());

    act(() => {
      result.current.reset();
    });

    expect(result.current.previewImage).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.processingTimeMs).toBeNull();
  });
});
