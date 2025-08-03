import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";

export default function ChatInterface() {
  return (
    <div className="w-screen h-screen flex justify-center bg-gradient-to-br  overflow-hidden">
      <div className="flex flex-col gap-2 w-[80%] ">
        <div className="w-full">
          <Header />
        </div>
        <ScrollArea className="h-screen p-10 pt-0 flex flex-col gap-2 relative">
          <div className="flex flex-col gap-2 pb-30">
            <AIMessage />
            <AIMessage />
            <AIMessage />
            <AIMessage />
            <AIMessage />
            <UserMessage />
            <AIProcess message={"Submitting your response"} isLoading />
            <UserInteraction
              options={[
                "A. Some option one",
                "B. Some Option two",
                "C. Select option three",
                "D. Some option 4",
              ]}
            />
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}

const AIMessage = () => {
  return (
    <div className="flex items-start gap-2">
      <div>
        <Avatar>
          <AvatarFallback>AI</AvatarFallback>
        </Avatar>
      </div>
      <div className="bg-primary/10 p-2 rounded-md mr-10">
        <p className="font-semibold">Question</p>
        <p>
          Lorem ipsum dolor sit amet consectetur adipisicing elit. Placeat
          numquam sapiente laboriosam doloremque possimus sint rerum eaque iure
          tempore deleniti veritatis repudiandae a iste nulla voluptas, tenetur
          suscipit nemo at. Lorem ipsum dolor sit amet consectetur adipisicing
          elit. Placeat numquam sapiente laboriosam doloremque possimus sint
          rerum eaque iure tempore deleniti veritatis repudiandae a iste nulla
          voluptas, tenetur suscipit nemo at.
        </p>
      </div>
    </div>
  );
};

const AIProcess = ({ message, isLoading }) => {
  return (
    <div className="flex gap-2">
      <Avatar>
        <AvatarFallback>AI</AvatarFallback>
      </Avatar>
      <span
        className={`p-2 italic text-foreground/90 bg-primary/10  rounded-lg text-sm ${
          isLoading ? "animate-pulse" : ""
        }`}
      >
        {message}
      </span>
    </div>
  );
};
const UserMessage = () => {
  return (
    <div className="flex items-start gap-2 w-full justify-end">
      <div className="bg-primary/10 p-2 rounded-md">
        <p className="font-semibold">Response</p>
        <p>A. Some selected option</p>
      </div>
      <div>
        <Avatar>
          <AvatarFallback>AI</AvatarFallback>
        </Avatar>
      </div>
    </div>
  );
};
const UserInteraction = ({ options }) => {
  return (
    <div className="flex items-end justify-end gap-2">
      <div>
        <h1 className="font-semibold">Choose From following options</h1>
        <div className="flex flex-col gap-1">
          {options.map((option) => (
            <p className="p-2 rounded-md bg-primary/20">{option}</p>
          ))}
        </div>
      </div>
      <div>
        <Avatar>
          <AvatarFallback>AI</AvatarFallback>
        </Avatar>
      </div>
    </div>
  );
};

const Header = () => {
  return <div className="w-full z-[999] h-20 "></div>;
};
