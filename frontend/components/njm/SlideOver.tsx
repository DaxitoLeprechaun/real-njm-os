"use client";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { cn } from "@/lib/utils";

interface SlideOverProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title?: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}

export default function SlideOver({
  open,
  onOpenChange,
  title,
  description,
  children,
  className,
}: SlideOverProps) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className={cn(
          // Override default w-3/4 to ensure ≥40% on desktop
          "sm:max-w-none w-full sm:w-[42%] glass-strong border-l border-white/[0.08] p-0",
          className
        )}
      >
        {(title || description) && (
          <SheetHeader className="px-6 pt-6 pb-4 border-b border-white/[0.06]">
            {title && <SheetTitle>{title}</SheetTitle>}
            {description && <SheetDescription>{description}</SheetDescription>}
          </SheetHeader>
        )}
        <div className="flex-1 overflow-y-auto px-6 py-5">{children}</div>
      </SheetContent>
    </Sheet>
  );
}
