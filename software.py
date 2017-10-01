from step import Step
from step import UserInputStep
from step import NoChildrenException



class Software(object):
    def __init__(self, user_supplied_id):
        self.user_supplied_id = user_supplied_id
        self.completed_steps = []

    def get_citation(self):
        my_step = UserInputStep()
        my_step.content = self.user_supplied_id
        self.completed_steps.append(my_step)

        cursor = 0
        while not self.completed_steps[-1].is_metadata:
            current_step = self.completed_steps[cursor]

            try:
                next_step = current_step.get_child()
            except NoChildrenException:
                cursor -= 1
                continue

            self.completed_steps.append(next_step)

            # set cursor to end of stack.
            cursor += len(self.completed_steps) - 1


    def get_metadata(self):
        metadata_step = self.completed_steps[-1]
        return metadata_step.content


    def get_provenance(self):
        ret = [s.to_dict() for s in self.completed_steps]
        return ret


    def to_dict(self):
        ret = {
            "metadata": self.get_metadata(),
            "provenance": self.get_provenance()
        }
        return ret