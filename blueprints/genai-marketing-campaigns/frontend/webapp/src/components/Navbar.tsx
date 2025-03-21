// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { useAuthenticator } from "@aws-amplify/ui-react";
import { IconLogout, IconPhotoAi as Icon } from "@tabler/icons-react";
import { Link, useNavigate } from "react-router-dom";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

export default function Navbar() {
  const {
    user: { username },
    signOut,
  } = useAuthenticator((context) => [context.user]);
  const navigate = useNavigate();

  const handleSignOut = () => {
    signOut();
    navigate("/");
  };

  const env = import.meta.env;

  return (
    <nav className="mb-3 flex w-full items-center justify-between border-b bg-white p-3 shadow-sm">
      <Link to="/">
        <div className="flex items-center text-gray-800 hover:text-opacity-80">
          <Icon className="mr-2" />
          <h1 className="text-md font-bold leading-8">{env.VITE_APP_NAME}</h1>
        </div>
      </Link>

      {env.VITE_APP_LOGO_URL !== "" && (
        <img className="md-hidden h-8" src={env.VITE_APP_LOGO_URL} />
      )}

      <div className="flex items-center gap-3">
        <Avatar className="h-8 w-8">
          <AvatarFallback>{username?.charAt(0).toUpperCase()}</AvatarFallback>
        </Avatar>
        <button
          onClick={handleSignOut}
          className="text-sm text-gray-800 hover:text-gray-600"
        >
          <span className="font-bold">
            <IconLogout size={24} />
          </span>
        </button>
      </div>
    </nav>
  );
}
