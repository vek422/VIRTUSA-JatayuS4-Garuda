import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";
import { ModeToggle } from "./mode-toggle";
import {
  FilePlus,
  Home,
  ListCheck,
  LogOut,
  Logs,
  ScrollText,
  Users,
} from "lucide-react";
import { Button } from "./ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { DropdownMenuItem } from "./ui/dropdown-menu";
import { Link, useNavigate } from "react-router-dom";
import { useLogoutMutation, useProfileQuery } from "@/api/authApi";
import { useAppDispatch } from "@/store";
import { clearCredentials } from "@/store/slices/authSlice";
const navItems = [
  {
    label: "Dashboard",
    icon: Home,
    url: "/recruiter/dashboard",
  },
  {
    label: "Tests",
    icon: ListCheck,
    url: "/recruiter/tests",
  },
  {
    label: "Create Test",
    icon: FilePlus,
    url: "/recruiter/test/create",
  },
  {
    label: "Candidates",
    icon: Users,
    url: "/recruiter/candidates",
  },
  {
    label: "Logs",
    icon: ScrollText,
    url: "/recruiter/logs",
  },
];

export function AppSidebar() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();

  // Fetch user profile - this will automatically fetch when component mounts
  const {
    data: profile,
    isLoading: profileLoading,
    error: profileError,
  } = useProfileQuery();
  console.log("Profile data:", profile);
  const [logoutMutation, { isLoading: logoutLoading }] = useLogoutMutation();

  const handleLogout = async () => {
    try {
      await logoutMutation().unwrap();
    } catch (error) {
      console.log("Logout API failed (this is OK):", error);
    } finally {
      // Clear Redux store (this will also clear persisted state)
      dispatch(clearCredentials());
      navigate("/login");
    }
  };

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((word) => word.charAt(0))
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };
  return (
    <Sidebar>
      <SidebarHeader>
        <div className="flex items-center justify-between p-4">
          <h1 className="text-2xl font-bold text-primary">Skill Sync</h1>
          <ModeToggle />
        </div>
      </SidebarHeader>
      <SidebarContent className="px-4">
        <SidebarMenu>
          {navItems.map((item) => (
            <SidebarMenuItem key={item.label}>
              <Link to={item.url} className="flex items-center gap-2">
                <SidebarMenuButton className="cursor-pointer">
                  <item.icon size={16} /> {item.label}
                </SidebarMenuButton>
              </Link>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarContent>
      <SidebarFooter>
        <DropdownMenu>
          <DropdownMenuTrigger className="h-14 flex gap-2 items-center hover:bg-muted p-2 rounded-md">
            <Avatar className="">
              <AvatarImage src="https://github.com/shadcn.png"></AvatarImage>
              <AvatarFallback>VK</AvatarFallback>
            </Avatar>
            <div>
              <p className="text-sm text-left">
                {profileLoading
                  ? "Loading..."
                  : profile?.name || "Unknown User"}
              </p>
              <p className="text-sm text-muted-foreground">
                {profileLoading ? "..." : profile?.email || "No email"}
              </p>
              <p className="text-sm text-left">
                {profileLoading ? "..." : profile?.role || "No role"}
              </p>
            </div>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-48">
            <DropdownMenuItem className="w-full">
              <Button
                variant="destructive"
                className="w-full"
                onClick={handleLogout}
                disabled={logoutLoading}
              >
                <LogOut />
                {logoutLoading ? "Logging out..." : "Logout"}
              </Button>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
