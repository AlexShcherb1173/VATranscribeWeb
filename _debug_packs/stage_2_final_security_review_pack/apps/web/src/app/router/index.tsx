import { createBrowserRouter, Navigate } from "react-router-dom";

import { AppShell } from "@/widgets/app-shell/AppShell";
import { ProtectedRoute } from "@/widgets/protected-route/ProtectedRoute";
import { BillingPage } from "@/pages/billing/BillingPage";
import { DashboardPage } from "@/pages/dashboard/DashboardPage";
import { DownloadsPage } from "@/pages/downloads/DownloadsPage";
import { FilesPage } from "@/pages/files/FilesPage";
import { JobsPage } from "@/pages/jobs/JobsPage";
import { LandingPage } from "@/pages/landing/LandingPage";
import { ProfilePage } from "@/pages/profile/ProfilePage";
import { ResultPage } from "@/pages/result/ResultPage";
import { SettingsPage } from "@/pages/settings/SettingsPage";
import { TranscriptionsPage } from "@/pages/transcriptions/TranscriptionsPage";
import { UpgradePage } from "@/pages/upgrade/UpgradePage";
import { PricingPage } from "@/pages/pricing/PricingPage";

export const router = createBrowserRouter([
  { path: "/", element: <LandingPage /> },
  { path: "/auth", element: <Navigate to="/" replace /> },
  { path: "/pricing", element: <PricingPage /> },
  {
    element: <ProtectedRoute />,
    children: [
      {
        path: "/app",
        element: <AppShell />,
        children: [
          { index: true, element: <DashboardPage /> },
          { path: "downloads", element: <DownloadsPage /> },
          { path: "files", element: <FilesPage /> },
          { path: "jobs", element: <JobsPage /> },
          { path: "transcriptions", element: <TranscriptionsPage /> },
          { path: "results/:transcriptId", element: <ResultPage /> },
          { path: "profile", element: <ProfilePage /> },
          { path: "billing", element: <BillingPage /> },
          { path: "upgrade", element: <UpgradePage /> },
          { path: "settings", element: <SettingsPage /> },
        ],
      },
    ],
  },
]);
