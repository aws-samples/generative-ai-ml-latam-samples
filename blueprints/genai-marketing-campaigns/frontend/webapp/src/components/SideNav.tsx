// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { Button } from "@/components/ui/button";
import { deleteCampaign, getCampaigns } from "@/lib/api";
import { useEffect, useState } from "react";
import { Campaign } from "@/contexts/campaign-context";
import { IconFilePlus, IconTrash } from "@tabler/icons-react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { useToast } from "@/components/ui/use-toast";
import { Skeleton } from "./ui/skeleton";

type SideNavState = {
  loading: boolean;
  list: Campaign[];
};

export default function SideNav() {
  const [items, setItems] = useState<SideNavState>({
    loading: true,
    list: [],
  });

  const [editMode, setEditMode] = useState<boolean>(false);

  const { toast } = useToast();

  useEffect(() => {
    const fetchItems = async () => {
      try {
        const campaigns = (await getCampaigns()) as Campaign[];
        setItems((prev) => ({ ...prev, loading: false, list: campaigns }));
      } catch (error) {
        console.error(error);
      }
    };

    fetchItems();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const confirmCampaignDeletion = async (campaign: Campaign) => {
    try {
      if (campaign.id) {
        await deleteCampaign(campaign.id);
        toast({
          title: "Campaign deleted",
          description: "The campaign was succesfully deleted",
          variant: "destructive",
        });

        setItems((prev) => ({
          ...prev,
          list: prev.list.filter((c) => c.id !== campaign.id),
        }));
      } else {
        throw new Error("Campaign ID not found");
      }
    } catch (error) {
      toast({
        title: "Something went wrong.",
        description: "The briefing could not be deleted",
      });
    }
  };

  return (
    <div className="flex flex-col gap-3 md:col-span-1">
      <div className="flex justify-between">
        <Button className="flex gap-2">
          <IconFilePlus /> New campaign
        </Button>
        <Button variant={"secondary"} onClick={() => setEditMode(!editMode)}>
          {editMode ? "Cancel" : "Edit"}
        </Button>
      </div>
      <div className="flex flex-col gap-3 text-sm">
        {items.loading && (
          <>
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </>
        )}

        {!items.loading &&
          items.list?.length > 0 &&
          items.list.map((campaign) => {
            return (
              <a
                key={campaign.id}
                href="#"
                className="group flex h-10 w-full items-center justify-between rounded-md border-transparent pl-3 pr-2 text-muted-foreground hover:bg-gray-100 hover:underline"
              >
                <span className="truncate">{campaign.name}</span>
                {editMode && (
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button className="h-auto p-1 hover:bg-red-500">
                        <IconTrash size={18} className="text-white" />
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>
                          Are you absolutely sure?
                        </AlertDialogTitle>
                        <AlertDialogDescription>
                          This action cannot be undone. This will permanently
                          delete the campaign removing data from our servers.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                          className="bg-destructive hover:bg-destructive"
                          onClick={() => confirmCampaignDeletion(campaign)}
                        >
                          Delete
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                )}
              </a>
            );
          })}
      </div>
    </div>
  );
}
