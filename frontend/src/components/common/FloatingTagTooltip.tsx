import React, { useState, useLayoutEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import styles from './FloatingTagTooltip.module.css';

export interface FloatingTagTooltipProps {
  text: string | null;
  targetRect: DOMRect | null;
}

export const FloatingTagTooltip: React.FC<FloatingTagTooltipProps> = ({
  text,
  targetRect,
}) => {
  const tooltipRef = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState<{ top: number; left: number }>({
    top: -9999,
    left: -9999,
  });

  useLayoutEffect(() => {
    if (!text || !targetRect || !tooltipRef.current) return;

    const tooltipEl = tooltipRef.current;
    const rect = tooltipEl.getBoundingClientRect();

    let top = targetRect.top - rect.height - 6;
    if (top < 8) {
      top = targetRect.bottom + 6;
    }

    let left = targetRect.left + (targetRect.width - rect.width) / 2;
    if (left + rect.width > window.innerWidth - 12) {
      left = window.innerWidth - rect.width - 12;
    }
    if (left < 12) left = 12;

    setPosition({ top, left });
  }, [text, targetRect]);

  if (!text || !targetRect) return null;

  return createPortal(
    <div
      ref={tooltipRef}
      className={styles.tooltipPortal}
      style={{ top: `${position.top}px`, left: `${position.left}px` }}
      role="tooltip"
    >
      {text}
    </div>,
    document.body
  );
};

