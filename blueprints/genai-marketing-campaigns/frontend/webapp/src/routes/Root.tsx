// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { Outlet } from "react-router-dom";
import NavBar from "@/components/Navbar";
import SideNav from "@/components/SideNav";
import CampaignContextProvider from "@/contexts/campaign-context";
import { Toaster } from "@/components/ui/toaster";

export default function Root() {
  return (
    <>
      <Toaster />
      <NavBar />
      <main className="grid gap-3 px-3 md:grid-cols-4">
        <SideNav />

        <div className=" md:col-span-3 pb-20">
          <CampaignContextProvider>
            <Outlet />
          </CampaignContextProvider>
        </div>
      </main>
    </>
  );
}
