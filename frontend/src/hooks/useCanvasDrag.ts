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
  selectedPerson: "person1" | "person2" | null;
  handleMouseDown: (e: React.MouseEvent<HTMLCanvasElement>) => void;
  handleMouseMove: (e: React.MouseEvent<HTMLCanvasElement>) => void;
  handleMouseUp: () => void;
  clearSelection: () => void;
}

const CLICK_THRESHOLD = 5; // pixels - below this is a click, not a drag

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
  const [selectedPerson, setSelectedPerson] = useState<"person1" | "person2" | null>(null);

  const canvasRef = useRef<DOMRect | null>(null);
  const mouseDownPos = useRef<{ x: number; y: number } | null>(null);

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
      mouseDownPos.current = { x: e.clientX, y: e.clientY };
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

  const handleMouseUp = useCallback(
    (e?: React.MouseEvent<HTMLCanvasElement>) => {
      if (!dragState.isDragging || !dragState.dragTarget) {
        // Click on empty area - deselect
        if (mouseDownPos.current && e) {
          const dx = Math.abs(e.clientX - mouseDownPos.current.x);
          const dy = Math.abs(e.clientY - mouseDownPos.current.y);
          if (dx < CLICK_THRESHOLD && dy < CLICK_THRESHOLD) {
            setSelectedPerson(null);
          }
        }
        mouseDownPos.current = null;
        return;
      }

      const deltaX = dragState.dragCurrentX - dragState.dragStartX;
      const deltaY = dragState.dragCurrentY - dragState.dragStartY;

      // Check if this was a click (minimal movement) vs a drag
      const pixelDeltaX = mouseDownPos.current && e
        ? Math.abs(e.clientX - mouseDownPos.current.x)
        : Math.abs(deltaX);
      const pixelDeltaY = mouseDownPos.current && e
        ? Math.abs(e.clientY - mouseDownPos.current.y)
        : Math.abs(deltaY);

      if (pixelDeltaX < CLICK_THRESHOLD && pixelDeltaY < CLICK_THRESHOLD) {
        // This was a click - toggle selection
        setSelectedPerson((prev) =>
          prev === dragState.dragTarget ? null : dragState.dragTarget
        );
      } else {
        // This was a drag - update position and keep selected
        const currentX = dragState.dragTarget === "person1" ? person1X : person2X;
        const currentYOffset = dragState.dragTarget === "person1" ? person1YOffset : person2YOffset;
        const newX = Math.max(0, Math.min(1, currentX + deltaX / outputWidth));
        const newYOffset = Math.max(-500, Math.min(500, currentYOffset + deltaY));
        onDragEnd(dragState.dragTarget, newX, newYOffset);
        setSelectedPerson(dragState.dragTarget);
      }

      mouseDownPos.current = null;
      setDragState({
        isDragging: false,
        dragTarget: null,
        dragStartX: 0,
        dragCurrentX: 0,
        dragStartY: 0,
        dragCurrentY: 0,
      });
    },
    [dragState, person1X, person2X, person1YOffset, person2YOffset, outputWidth, onDragEnd]
  );

  const clearSelection = useCallback(() => {
    setSelectedPerson(null);
  }, []);

  return { dragState, selectedPerson, handleMouseDown, handleMouseMove, handleMouseUp, clearSelection };
}
