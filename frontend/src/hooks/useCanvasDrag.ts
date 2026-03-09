import { useState, useCallback, useRef } from "react";
import type { BoundingBox } from "../types/index.ts";

interface DragState {
  isDragging: boolean;
  dragTarget: "person1" | "person2" | null;
  dragStartX: number;
  dragCurrentX: number;
}

interface UseCanvasDragProps {
  person1Bbox: BoundingBox | null;
  person2Bbox: BoundingBox | null;
  canvasWidth: number;
  outputWidth: number;
  person1X: number;
  person2X: number;
  onDragEnd: (target: "person1" | "person2", newX: number) => void;
}

interface UseCanvasDragReturn {
  dragState: DragState;
  handleMouseDown: (e: React.MouseEvent<HTMLCanvasElement>) => void;
  handleMouseMove: (e: React.MouseEvent<HTMLCanvasElement>) => void;
  handleMouseUp: () => void;
}

export function useCanvasDrag({
  person1Bbox,
  person2Bbox,
  canvasWidth,
  outputWidth,
  person1X,
  person2X,
  onDragEnd,
}: UseCanvasDragProps): UseCanvasDragReturn {
  const [dragState, setDragState] = useState<DragState>({
    isDragging: false,
    dragTarget: null,
    dragStartX: 0,
    dragCurrentX: 0,
  });

  const canvasRef = useRef<DOMRect | null>(null);

  const getCanvasX = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>): number => {
      const rect = e.currentTarget.getBoundingClientRect();
      canvasRef.current = rect;
      return ((e.clientX - rect.left) / rect.width) * outputWidth;
    },
    [outputWidth]
  );

  const hitTest = useCallback(
    (canvasX: number): "person1" | "person2" | null => {
      if (!person1Bbox || !person2Bbox) return null;
      const scale = canvasWidth > 0 ? outputWidth / canvasWidth : 1;

      const p1CenterX = person1X * outputWidth;
      const p1HalfW = (person1Bbox.width * scale) / 2;
      if (canvasX >= p1CenterX - p1HalfW && canvasX <= p1CenterX + p1HalfW) {
        return "person1";
      }

      const p2CenterX = person2X * outputWidth;
      const p2HalfW = (person2Bbox.width * scale) / 2;
      if (canvasX >= p2CenterX - p2HalfW && canvasX <= p2CenterX + p2HalfW) {
        return "person2";
      }

      return null;
    },
    [person1Bbox, person2Bbox, canvasWidth, outputWidth, person1X, person2X]
  );

  const handleMouseDown = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      const canvasX = getCanvasX(e);
      const target = hitTest(canvasX);
      if (target) {
        setDragState({
          isDragging: true,
          dragTarget: target,
          dragStartX: canvasX,
          dragCurrentX: canvasX,
        });
      }
    },
    [getCanvasX, hitTest]
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      if (!dragState.isDragging) return;
      const canvasX = getCanvasX(e);
      setDragState((prev) => ({ ...prev, dragCurrentX: canvasX }));
    },
    [dragState.isDragging, getCanvasX]
  );

  const handleMouseUp = useCallback(() => {
    if (!dragState.isDragging || !dragState.dragTarget) return;

    const deltaX = dragState.dragCurrentX - dragState.dragStartX;
    const currentX = dragState.dragTarget === "person1" ? person1X : person2X;
    const newX = Math.max(0, Math.min(1, currentX + deltaX / outputWidth));

    onDragEnd(dragState.dragTarget, newX);

    setDragState({
      isDragging: false,
      dragTarget: null,
      dragStartX: 0,
      dragCurrentX: 0,
    });
  }, [dragState, person1X, person2X, outputWidth, onDragEnd]);

  return { dragState, handleMouseDown, handleMouseMove, handleMouseUp };
}
