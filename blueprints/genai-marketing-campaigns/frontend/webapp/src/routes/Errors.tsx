// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { IconArrowLeft } from "@tabler/icons-react";
import { Link, useRouteError } from "react-router-dom";

export default function Errors() {
  const error: unknown = useRouteError();

  return (
    <main
      id="error-page"
      className="flex h-screen items-center justify-center bg-gray-800"
    >
      <div className="mx-4 flex w-full max-w-xl flex-col gap-5 rounded-xl border border-gray-200 bg-white p-4 text-gray-700 drop-shadow-lg">
        <div className="flex flex-col gap-1">
          <h3 className="text-lg font-bold">Oops!</h3>
          <p className="text-xs text-gray-500">
            Sorry, but an unexpected error has occurred.
          </p>
        </div>
        {!!error && (
          <pre className="whitespace-pre-wrap rounded-md border border-gray-400 bg-gray-100 p-2 text-xs text-gray-950">
            {JSON.stringify(error, null, 2)}
          </pre>
        )}

        <Link
          to="/"
          className="max-w-24 flex items-center justify-center gap-3 rounded-md bg-gray-800 p-2 text-xs font-bold text-white"
        >
          <IconArrowLeft className="h-5 w-5" />
          go home
        </Link>

        <footer className="border-t border-t-gray-200 pt-3 font-mono text-[10px] text-gray-500">
          Built with <span className="font-sans">❤️</span> by{" "}
          <span className="font-bold">PACE</span>
        </footer>
      </div>
    </main>
  );
}
