// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { useAuthenticator } from "@aws-amplify/ui-react";
import { Navigate } from "react-router";

export function Logout() {
  const { signOut } = useAuthenticator((context) => [context.route]);
  signOut();

  return <Navigate to={"/login"} replace />;
}
