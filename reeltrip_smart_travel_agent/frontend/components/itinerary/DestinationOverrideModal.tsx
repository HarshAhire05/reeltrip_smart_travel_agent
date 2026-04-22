"use client";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface DestinationOverrideModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  originalDestination: string;
  newDestination: string;
}

export function DestinationOverrideModal({
  open,
  onOpenChange,
  onConfirm,
  originalDestination,
  newDestination,
}: DestinationOverrideModalProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <span className="text-2xl">⚠️</span>
            Changing Destination
          </AlertDialogTitle>
          <AlertDialogDescription className="space-y-3 pt-2">
            <p>
              You are changing the destination from{" "}
              <span className="font-semibold text-foreground">
                {originalDestination}
              </span>{" "}
              to{" "}
              <span className="font-semibold text-foreground">
                {newDestination}
              </span>
              .
            </p>
            <p>
              <strong>
                This will rebuild your full itinerary from scratch.
              </strong>
            </p>
            <ul className="list-disc list-inside space-y-1 text-sm">
              <li>All current plans will be replaced</li>
              <li>Flights, hotels, and activities will be regenerated</li>
              <li>This action cannot be undone (except via Undo button)</li>
            </ul>
            <p className="text-sm text-muted-foreground pt-2">
              Are you sure you want to continue?
            </p>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            Change Destination
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
