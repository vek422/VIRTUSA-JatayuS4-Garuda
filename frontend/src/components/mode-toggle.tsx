import { useTheme } from "./theme-provider";
import type { FC } from "react";
import { Button } from "./ui/button";
import { Moon, Sun } from "lucide-react";
export const ModeToggle: FC = () => {
  const { setTheme, theme } = useTheme();
  return (
    <Button
      variant={"outline"}
      className="rounded-full p-4"
      size={"icon"}
      onClick={() => setTheme(theme == "light" ? "dark" : "light")}
    >
      <Sun className="fixed rotate-0 scale-100 duration-500 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon className="fixed rotate-90 scale-0 duration-500 transition-all dark:rotate-0 dark:scale-100" />
    </Button>
  );
};
