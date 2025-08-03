import { Outlet } from "react-router-dom";
import { SidebarProvider, SidebarTrigger } from "../ui/sidebar";
import { AppSidebar } from "../AppSidebar";
export function RecruiterLayout() {
  return (
    <div className="w-full h-screen flex flex-col bg-background overflow-hidden">
      <SidebarProvider>
        <AppSidebar />
        <main className="flex-1 p-4 overflow-y-auto relative">
          <div className="container pl-4 pt-1 overflow-hidden">
            <Outlet />
          </div>
        </main>
      </SidebarProvider>
    </div>
  );
}
