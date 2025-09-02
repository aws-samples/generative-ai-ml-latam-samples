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

import HeaderGradient from "@/components/HeaderGradient";
import { Outlet } from "react-router";

export function Root() {
  return (
    <main className="h-screen flex flex-col overflow-hidden max-w-full">
      <HeaderGradient
        lightColors={["#9333ea", "#4f46e5"]}
        darkColors={["#7c2d12", "#3730a3"]}
        lightOpacity={75}
        darkOpacity={75}
        animationDuration={15}
        animate={true}
        angle="120deg"
      />
      <div className="flex-1 overflow-hidden max-w-full">
        <Outlet />
      </div>
    </main>
  );
}
