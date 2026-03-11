import { useState, useCallback, useRef } from "react";

interface DragState {
  isDragging: boolean;
  dragTarget: "person1" | "person2" | null;
  dragStartX: number;
  dragCurrentX: number;
  dragStartY: number;
  dragCurrentY: number;
}

export interface PersonHighlightForDrag {
  centerX: number; // 0-1 ratio
  topY: number;    // preview pixels
  width: number;   // preview pixels
  height: number;  // preview pixels
}

interface UseCanvasDragProps {
  person1Highlight: PersonHighlightForDrag | null;
  person2Highlight: PersonHighlightForDrag | null;
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
  person1Highlight,
  person2Highlight,
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

  const mouseDownPos = useRef<{ x: number; y: number } | null>(null);
  const displaySizeRef = useRef<{ w: number; h: number }>({ w: 640, h: 640 });

  // Returns position in CSS pixels relative to canvas display area
  const getCanvasPos = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>): { x: number; y: number } => {
      const rect = e.currentTarget.getBoundingClientRect();
      return {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      };
    },
    []
  );

  // Get display dimensions for ratio conversion
  const getDisplaySize = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>): { w: number; h: number } => {
      const rect = e.currentTarget.getBoundingClientRect();
      return { w: rect.width, h: rect.height };
    },
    []
  );

  // Hit test using highlight positions (matches actual visual positions on canvas)
  const hitTest = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>): "person1" | "person2" | null => {
      if (!person1Highlight && !person2Highlight) return null;

      const rect = e.currentTarget.getBoundingClientRect();
      // Get mouse position in 0-1 ratios relative to canvas display
      const ratioX = (e.clientX - rect.left) / rect.width;
      const ratioY = (e.clientY - rect.top) / rect.height;
      // Get canvas internal dimensions (preview pixels)
      const canvas = e.currentTarget;
      const px = ratioX * canvas.width;
      const py = ratioY * canvas.height;

      // Check person2 first (front layer by default), then person1
      // This way clicking on overlapping area selects the front person
      const checks: Array<{ key: "person1" | "person2"; hl: PersonHighlightForDrag }> = [];
      if (person2Highlight) checks.push({ key: "person2", hl: person2Highlight });
      if (person1Highlight) checks.push({ key: "person1", hl: person1Highlight });

      for (const { key, hl } of checks) {
        const cx = hl.centerX * canvas.width;
        const left = cx - hl.width / 2;
        const right = cx + hl.width / 2;
        const top = hl.topY;
        const bottom = hl.topY + hl.height;
        if (px >= left && px <= right && py >= top && py <= bottom) {
          return key;
        }
      }

      return null;
    },
    [person1Highlight, person2Highlight]
  );

  const handleMouseDown = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      e.preventDefault();
      const pos = getCanvasPos(e);
      const ds = getDisplaySize(e);
      const target = hitTest(e);
      mouseDownPos.current = { x: e.clientX, y: e.clientY };
      displaySizeRef.current = ds;
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
    [getCanvasPos, getDisplaySize, hitTest]
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      if (!dragState.isDragging) return;
      e.preventDefault();
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

      // deltaX/deltaY are in CSS pixels (display space)
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
        // This was a drag - convert CSS pixel delta to output-space values
        const { w: displayW, h: displayH } = displaySizeRef.current;
        const currentX = dragState.dragTarget === "person1" ? person1X : person2X;
        const currentYOffset = dragState.dragTarget === "person1" ? person1YOffset : person2YOffset;
        // X: convert CSS pixels to 0-1 ratio change
        const newX = Math.max(-0.5, Math.min(1.5, currentX + deltaX / displayW));
        // Y: convert CSS pixels to output pixels proportionally
        const yDeltaInOutput = (deltaY / displayH) * outputHeight;
        const newYOffset = Math.max(-2000, Math.min(2000, currentYOffset + yDeltaInOutput));
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
    [dragState, person1X, person2X, person1YOffset, person2YOffset, outputHeight, onDragEnd]
  );

  const clearSelection = useCallback(() => {
    setSelectedPerson(null);
  }, []);

  return { dragState, selectedPerson, handleMouseDown, handleMouseMove, handleMouseUp, clearSelection };
}
