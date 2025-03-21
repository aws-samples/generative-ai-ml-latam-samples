// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

export type StepProps = {
  children: React.ReactNode;
  number: number;
  title: string;
  description?: string;
};

export default function StepContainer({
  children,
  number,
  title,
  description,
}: StepProps) {
  return (
    <section className="step flex flex-col gap-6">
      <header className="flex items-center gap-4">
        <div
          className={`flex h-12 w-12 items-center justify-center rounded-full bg-yellow-300 text-center text-xl font-extrabold text-gray-950`}
        >
          {number}
        </div>
        <div className="flex flex-col gap-1">
          <div className="text-lg font-bold">{title}</div>
          {description && (
            <div className="text-sm text-gray-400">{description}</div>
          )}
        </div>
      </header>
      <div className="pl-16">{children}</div>
    </section>
  );
}
