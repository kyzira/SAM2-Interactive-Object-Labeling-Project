class RadioButtonManagement:
    def __init__(self):
        self.__observation_list = []

    def add_observation(self, observation):
        if observation:
            counter = 0
            new_observation = f"{observation} {counter}"

            while new_observation in self.__observation_list:
                counter += 1
                new_observation = f"{observation} {counter}" 

            if observation not in self.__observation_list:
                self.__observation_list.append(new_observation)      

    def remove_observations(self, observation_list):
        for observation in observation_list:
            self.__observation_list.remove(observation)

    def get_observation_list(self):
        return self.__observation_list
