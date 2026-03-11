import type {
  SegmentResponse,
  MergeResponse,
  MergeRequest,
  HealthResponse,
  DetectRegionsResponse,
  EraseResponse,
  AppError,
  ApiError,
} from "../types/index.ts";

const BASE_URL = "/api";

function createAppError(status: number, body: ApiError): AppError {
  switch (body.error) {
    case "invalid_image":
    case "file_too_large":
      return {
        type: "validation",
        message: body.message,
        detail: body.detail,
        retryable: false,
      };
    case "segmentation_failed":
      return {
        type: "segmentation",
        message: body.message,
        detail: body.detail,
        retryable: false,
      };
    case "invalid_segment_id":
      return {
        type: "merge",
        message: body.message,
        detail: body.detail,
        retryable: true,
      };
    case "merge_failed":
    case "internal_error":
      return {
        type: "unknown",
        message: body.message,
        detail: body.detail,
        retryable: status < 500 ? false : true,
      };
    default:
      return {
        type: "unknown",
        message: body.message || "不明なエラーが発生しました。",
        detail: body.detail,
        retryable: true,
      };
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let body: ApiError;
    try {
      const raw = await response.json();
      // Handle Pydantic 422 validation errors (detail is an array of objects)
      if (response.status === 422 && Array.isArray(raw.detail)) {
        const msgs = raw.detail.map((d: { loc?: string[]; msg?: string }) =>
          `${(d.loc ?? []).join(".")}: ${d.msg ?? "validation error"}`
        );
        body = {
          error: "validation_error",
          message: "入力パラメータが不正です。",
          detail: msgs.join("; "),
        };
      } else {
        body = raw as ApiError;
      }
    } catch {
      body = {
        error: "internal_error",
        message: "サーバー内部エラーが発生しました。",
      };
    }
    throw createAppError(response.status, body);
  }
  return (await response.json()) as T;
}

export async function segmentImage(file: File): Promise<SegmentResponse> {
  const formData = new FormData();
  formData.append("image", file);

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}/segment`, {
      method: "POST",
      body: formData,
    });
  } catch {
    throw {
      type: "network",
      message: "サーバーに接続できません。起動を確認してください。",
      retryable: true,
    } satisfies AppError;
  }

  return handleResponse<SegmentResponse>(response);
}

export async function mergeImages(request: MergeRequest): Promise<MergeResponse> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}/merge`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
  } catch {
    throw {
      type: "network",
      message: "サーバーに接続できません。起動を確認してください。",
      retryable: true,
    } satisfies AppError;
  }

  return handleResponse<MergeResponse>(response);
}

export async function detectRegions(segId: string): Promise<DetectRegionsResponse> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}/detect-regions/${segId}`, {
      method: "POST",
    });
  } catch {
    throw {
      type: "network",
      message: "サーバーに接続できません。起動を確認してください。",
      retryable: true,
    } satisfies AppError;
  }

  return handleResponse<DetectRegionsResponse>(response);
}

export async function eraseRegions(
  segId: string,
  regionIds: number[]
): Promise<EraseResponse> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}/erase-regions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ seg_id: segId, region_ids: regionIds }),
    });
  } catch {
    throw {
      type: "network",
      message: "サーバーに接続できません。起動を確認してください。",
      retryable: true,
    } satisfies AppError;
  }

  return handleResponse<EraseResponse>(response);
}

export async function eraseManual(
  segId: string,
  strokes: { x: number; y: number; radius: number }[],
  displayWidth: number,
  displayHeight: number
): Promise<EraseResponse> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}/erase-manual`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        seg_id: segId,
        strokes,
        display_width: displayWidth,
        display_height: displayHeight,
      }),
    });
  } catch {
    throw {
      type: "network",
      message: "サーバーに接続できません。起動を確認してください。",
      retryable: true,
    } satisfies AppError;
  }

  return handleResponse<EraseResponse>(response);
}

export async function healthCheck(): Promise<HealthResponse> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}/health`);
  } catch {
    throw {
      type: "network",
      message: "サーバーに接続できません。起動を確認してください。",
      retryable: true,
    } satisfies AppError;
  }

  return handleResponse<HealthResponse>(response);
}
