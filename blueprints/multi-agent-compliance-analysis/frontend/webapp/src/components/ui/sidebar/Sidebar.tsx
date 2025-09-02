// MIT No Attribution
//
// Copyright 2025 Amazon Web Services
//
// Permission is hereby granted, free of charge, to any person obtaining a copy of this
// software and associated documentation files (the "Software"), to deal in the Software
// without restriction, including without limitation the rights to use, copy, modify,
// merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
// permit persons to whom the Software is furnished to do so.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
// INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
// PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
// HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
// OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
// SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import React, { ReactNode, useEffect } from "react";
import { useSidebar } from "./SidebarContext";
import { cn } from "@/lib/utils";
import { SparklesIcon, X } from "lucide-react";
import { Button } from "../button";
import { useMediaQuery } from "@/hooks/use-media-query";

interface SidebarProps {
  children: ReactNode;
  title?: string;
  width?: string;
  className?: string;
}

const Sidebar: React.FC<SidebarProps> = ({
  children,
  title = "Sidebar",
  width = "400px",
  className = "",
}) => {
  const { isOpen, setOpen } = useSidebar();
  const isMobile = useMediaQuery("(max-width: 768px)");

  // Close sidebar when pressing escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };

    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [setOpen]);

  return (
    <div
      className={cn(
        "sidebar-container fixed right-0 top-0 z-10 flex h-full flex-col border-l border-neutral-200 bg-white shadow-lg transition-all duration-300 ease-in-out",
        isMobile && "w-full",
        className,
      )}
      style={{
        width: isMobile ? "100%" : width,
        transform: `translateX(${isOpen ? 0 : 100}%)`,
        pointerEvents: isOpen ? "auto" : "none",
      }}
    >
      <div className="sidebar-header flex items-center justify-between border-b border-neutral-200 bg-white p-2">
        <div className="flex items-center gap-2">
          <SparklesIcon className="h-5 w-5" />
          <h3 className="text-md font-medium">{title}</h3>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setOpen(false)}
          className="h-8 w-8"
          aria-label="Fechar sidebar"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      <div className="sidebar-content flex-1 overflow-y-auto p-4">
        {children}
      </div>
    </div>
  );
};

export default Sidebar;
