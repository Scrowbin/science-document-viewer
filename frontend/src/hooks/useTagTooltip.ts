import { useState } from 'react';

export function useTagTooltip() {
  const [tooltipState, setTooltipState] = useState<{
    text: string | null;
    targetRect: DOMRect | null;
  }>({ text: null, targetRect: null });

  const showTooltip = (text: string, e: React.MouseEvent<HTMLElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setTooltipState({ text, targetRect: rect });
  };

  const hideTooltip = () => {
    setTooltipState({ text: null, targetRect: null });
  };

  return {
    tooltipProps: tooltipState,
    showTooltip,
    hideTooltip,
  };
}
