class RadioButtonManagement:
    def __init__(self):
        self.__observation_list = []

    def add_observation(self, observation):
        if observation and observation not in self.__observation_list:
            self.__observation_list.append(observation)      

    def remove_observations(self, observation_list):
        for observation in observation_list:
            self.__observation_list.remove(observation)

    def get_observation_list(self):
        return self.__observation_list
