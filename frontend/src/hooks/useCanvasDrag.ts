import { useState, useCallback, useRef } from "react";
import type { BoundingBox } from "../types/index.ts";

interface DragState {
  isDragging: boolean;
  dragTarget: "person1" | "person2" | null;
  dragStartX: number;
  dragCurrentX: number;
  dragStartY: number;
  dragCurrentY: number;
}

interface UseCanvasDragProps {
  person1Bbox: BoundingBox | null;
  person2Bbox: BoundingBox | null;
  canvasWidth: number;
  outputWidth: number;
  outputHeight: number;
  person1X: number;
  person2X: number;
  person1YOffset: number;
  person2YOffset: number;
  onDragEnd: (target: "person1" | "person2", newX: number, newYOffset: number) => void;
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
  outputHeight,
  person1X,
  person2X,
  person1YOffset,
  person2YOffset,
  onDragEnd,
}: UseCanvasDragProps): UseCanvasDragReturn {
  const [dragState, setDragState] = useState<DragState>({
    isDragging: false,
    dragTarget: null,
    dragStartX: 0,
    dragCurrentX: 0,
    dragStartY: 0,
    dragCurrentY: 0,
  });

  const canvasRef = useRef<DOMRect | null>(null);

  const getCanvasPos = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>): { x: number; y: number } => {
      const rect = e.currentTarget.getBoundingClientRect();
      canvasRef.current = rect;
      return {
        x: ((e.clientX - rect.left) / rect.width) * outputWidth,
        y: ((e.clientY - rect.top) / rect.height) * outputHeight,
      };
    },
    [outputWidth, outputHeight]
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
      const pos = getCanvasPos(e);
      const target = hitTest(pos.x);
      if (target) {
        setDragState({
          isDragging: true,
          dragTarget: target,
          dragStartX: pos.x,
          dragCurrentX: pos.x,
          dragStartY: pos.y,
          dragCurrentY: pos.y,
        });
      }
    },
    [getCanvasPos, hitTest]
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      if (!dragState.isDragging) return;
      const pos = getCanvasPos(e);
      setDragState((prev) => ({ ...prev, dragCurrentX: pos.x, dragCurrentY: pos.y }));
    },
    [dragState.isDragging, getCanvasPos]
  );

  const handleMouseUp = useCallback(() => {
    if (!dragState.isDragging || !dragState.dragTarget) return;

    const deltaX = dragState.dragCurrentX - dragState.dragStartX;
    const deltaY = dragState.dragCurrentY - dragState.dragStartY;
    const currentX = dragState.dragTarget === "person1" ? person1X : person2X;
    const currentYOffset = dragState.dragTarget === "person1" ? person1YOffset : person2YOffset;
    const newX = Math.max(0, Math.min(1, currentX + deltaX / outputWidth));
    const newYOffset = Math.max(-500, Math.min(500, currentYOffset + deltaY));

    onDragEnd(dragState.dragTarget, newX, newYOffset);

    setDragState({
      isDragging: false,
      dragTarget: null,
      dragStartX: 0,
      dragCurrentX: 0,
      dragStartY: 0,
      dragCurrentY: 0,
    });
  }, [dragState, person1X, person2X, person1YOffset, person2YOffset, outputWidth, onDragEnd]);

  return { dragState, handleMouseDown, handleMouseMove, handleMouseUp };
}
