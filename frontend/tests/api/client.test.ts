import { describe, it, expect, vi, beforeEach } from "vitest";
import { segmentImage, mergeImages, healthCheck } from "../../src/api/client.ts";

describe("API Client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe("segmentImage", () => {
    it("sends FormData with image file", async () => {
      const mockResponse = {
        id: "seg-123",
        segmented_image: "data:image/png;base64,abc",
        bbox: { x: 0, y: 0, width: 100, height: 200 },
        foot_y: 190,
        original_size: { width: 640, height: 480 },
        processing_time_ms: 1500,
      };

      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const file = new File(["dummy"], "test.jpg", { type: "image/jpeg" });
      const result = await segmentImage(file);

      expect(fetch).toHaveBeenCalledWith("/api/segment", {
        method: "POST",
        body: expect.any(FormData),
      });
      expect(result.id).toBe("seg-123");
      expect(result.foot_y).toBe(190);
    });

    it("throws AppError on network failure", async () => {
      globalThis.fetch = vi.fn().mockRejectedValue(new Error("Network error"));

      const file = new File(["dummy"], "test.jpg", { type: "image/jpeg" });
      await expect(segmentImage(file)).rejects.toMatchObject({
        type: "network",
        retryable: true,
      });
    });

    it("throws AppError on API error response", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 400,
        json: () =>
          Promise.resolve({
            error: "invalid_image",
            message: "Invalid image format",
          }),
      });

      const file = new File(["dummy"], "test.jpg", { type: "image/jpeg" });
      await expect(segmentImage(file)).rejects.toMatchObject({
        type: "validation",
        retryable: false,
      });
    });

    it("handles non-JSON error response", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: () => Promise.reject(new Error("not json")),
      });

      const file = new File(["dummy"], "test.jpg", { type: "image/jpeg" });
      await expect(segmentImage(file)).rejects.toMatchObject({
        type: "unknown",
        retryable: true,
      });
    });
  });

  describe("mergeImages", () => {
    it("sends JSON request body", async () => {
      const mockResponse = {
        merged_image: "data:image/png;base64,merged",
        processing_time_ms: 2000,
        output_size: { width: 1024, height: 1024 },
      };

      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const request = {
        image1_id: "id-1",
        image2_id: "id-2",
        settings: {
          background_color: "#FFFFFF",
          output_width: 1024,
          output_height: 1024,
          person1: { x: 0.3, y_offset: 0, scale: 1.0 },
          person2: { x: 0.7, y_offset: 0, scale: 1.0 },
          shadow: { enabled: true, intensity: 0.5 },
          color_correction: true,
        },
        preview_mode: true,
      };

      const result = await mergeImages(request);

      expect(fetch).toHaveBeenCalledWith("/api/merge", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      });
      expect(result.merged_image).toBe("data:image/png;base64,merged");
    });

    it("throws AppError on network failure", async () => {
      globalThis.fetch = vi.fn().mockRejectedValue(new Error("Network error"));

      await expect(
        mergeImages({
          image1_id: "1",
          image2_id: "2",
          settings: {
            background_color: "#FFF",
            output_width: 100,
            output_height: 100,
            person1: { x: 0.3, y_offset: 0, scale: 1 },
            person2: { x: 0.7, y_offset: 0, scale: 1 },
            shadow: { enabled: false, intensity: 0 },
            color_correction: false,
          },
          preview_mode: false,
        })
      ).rejects.toMatchObject({
        type: "network",
        retryable: true,
      });
    });
  });

  describe("healthCheck", () => {
    it("returns health response", async () => {
      const mockResponse = {
        status: "healthy",
        rembg_loaded: true,
        version: "1.0.0",
      };

      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await healthCheck();
      expect(result.status).toBe("healthy");
      expect(result.rembg_loaded).toBe(true);
    });

    it("throws on network failure", async () => {
      globalThis.fetch = vi.fn().mockRejectedValue(new Error("Offline"));

      await expect(healthCheck()).rejects.toMatchObject({
        type: "network",
      });
    });
  });
});
