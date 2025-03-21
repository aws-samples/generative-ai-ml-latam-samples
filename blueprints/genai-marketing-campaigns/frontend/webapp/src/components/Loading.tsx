// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import Spinner from "@/components/Spinner";

export default function Loading() {
  return (
    <div className="flex h-[calc(100vh-57px)] w-full items-center justify-center">
      <Spinner className=" text-violet-500" />
    </div>
  );
}
