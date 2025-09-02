// Copyright 2025 Amazon.com, Inc. or its affiliates. All Rights Reserved.]
// SPDX-License-Identifier: LicenseRef-.amazon.com.-AmznSL-1.0
// Licensed under the Amazon Software License  http://aws.amazon.com/asl/

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      "@routes": path.resolve(__dirname, "src/routes"),
      "@components": path.resolve(__dirname, "src/components"),
      "@loaders": path.resolve(__dirname, "src/loaders"),
      "@lib": path.resolve(__dirname, "src/lib"),
    },
  },
});
