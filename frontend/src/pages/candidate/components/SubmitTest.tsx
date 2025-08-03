import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTrigger,
} from "@/components/ui/dialog";

export default function SubmitTest({
  completeAssessment,
}: {
  completeAssessment: () => void;
}) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant={"destructive"}>Submit Assessment</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <h1 className="text-destructive text-xl font-semibold text-center">
            Warning!
          </h1>
        </DialogHeader>
        <DialogDescription className="text-lg text-center">
          You are about to submit the test, this action cannot be undone!!
        </DialogDescription>
        <DialogFooter className="">
          <DialogClose asChild>
            <Button variant={"outline"}>Close</Button>
          </DialogClose>
          <Button variant={"destructive"} onClick={completeAssessment}>
            Submit
          </Button>
        </DialogFooter>
      </DialogContent>
      <DialogClose />
    </Dialog>
  );
}
