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

import { Amplify } from "aws-amplify";
import { Authenticator } from "@aws-amplify/ui-react";
import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider, createBrowserRouter } from "react-router";

import "./index.css";
import "./lib/i18n";

import {
  RequireAuth,
  Login,
  Errors,
  Logout,
  Root,
  JobsManagement,
  KnowledgeBase,
} from "@/routes";
import { fetchAuthSession } from "aws-amplify/auth";

const env = import.meta.env; // Vite environment variables

Amplify.configure(
  {
    Auth: {
      Cognito: {
        userPoolId: env.VITE_COGNITO_USER_POOL_ID,
        userPoolClientId: env.VITE_COGNITO_USER_POOL_CLIENT_ID,
        identityPoolId: env.VITE_COGNITO_IDENTITY_POOL_ID,
      },
    },
    API: {
      REST: {
        [env.VITE_API_NAME]: {
          endpoint: env.VITE_API_GATEWAY_REST_API_ENDPOINT,
          region: env.VITE_AWS_REGION,
        },
      },
    },
  },
  {
    API: {
      REST: {
        headers: async () => ({
          Authorization: (
            await fetchAuthSession()
          ).tokens?.idToken?.toString() as string,
        }),
      },
    },
  },
);

const router = createBrowserRouter([
  {
    path: "/",
    errorElement: <Errors />,
    children: [
      {
        element: (
          <RequireAuth>
            <Root />
          </RequireAuth>
        ),
        children: [
          {
            index: true,
            element: <JobsManagement />,
          },
          {
            path: "analysis",
            element: <JobsManagement />,
          },
          {
            path: "knowledge-base",
            element: <KnowledgeBase />,
          },
        ],
      },
      {
        path: "login",
        element: <Login />,
      },
      {
        path: "logout",
        element: <Logout />,
      },
      {
        path: "errors",
        element: <Errors />,
      },
    ],
  },
]);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Authenticator.Provider>
      <RouterProvider router={router} />
    </Authenticator.Provider>
  </React.StrictMode>,
);
