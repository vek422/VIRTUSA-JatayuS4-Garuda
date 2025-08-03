import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
} from "@/components/ui/navigation-menu";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ModeToggle } from "@/components/mode-toggle";
import { LogOut } from "lucide-react";
import { cn } from "@/lib/utils";

export default function CandidatesLayout() {
  const location = useLocation();
  const navigate = useNavigate();

  const isActive = (path: string) => location.pathname === path;

  const navigationItems = [
    { label: "Home", path: "/candidate/" },
    { label: "All Tests", path: "/candidate/all-tests" },
  ];

  const handleLogout = () => {
    // Add logout logic here
    console.log("Logging out...");
    navigate("/login");
  };

  return (
    <div className="w-full h-screen bg-background">
      <nav className="h-14 w-full border-b px-4 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center">
          <Link
            className="text-xl text-primary font-semibold hover:bg-transparent p-0"
            to={"/candidate"}
          >
            Skill Sync
          </Link>
        </div>

        {/* Navigation Menu */}
        <NavigationMenu>
          <NavigationMenuList>
            {navigationItems.map((item) => (
              <NavigationMenuItem key={item.path}>
                <NavigationMenuLink asChild className={cn(
                  "cursor-pointer px-3 py-2 rounded-md text-sm font-medium transition-colors",
                  isActive(item.path) && "bg-accent text-accent-foreground"
                )}>
                  <Link to={item.path}>{item.label}</Link>
                </NavigationMenuLink>
              </NavigationMenuItem>
            ))}
          </NavigationMenuList>
        </NavigationMenu>

        {/* Right side - Theme toggle and Profile */}
        <div className="flex items-center gap-2">
          <ModeToggle />

          {/* Profile Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                <Avatar className="">
                  <AvatarImage src="/placeholder-avatar.jpg" alt="Profile" />
                  <AvatarFallback>CN</AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end" forceMount>
              <DropdownMenuItem onClick={handleLogout}>
                <LogOut className="mr-2 h-4 w-4" />
                <span>Logout</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </nav>
      <Outlet />
    </div>
  );
}
