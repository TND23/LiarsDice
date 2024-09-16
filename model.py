import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import os

class Linear_QNet(nn.Module):
    def __init__(self, input, hidden, output):
        super().__init__()
        self.linearA = nn.Linear(input, hidden)
        self.linearB = nn.Linear(hidden, output)

    def forward(self, X):
        X = F.relu(self.linearA(X))
        X = self.linearB(X)
        return X

    def persist(self, file_name, path):
        if not os.path.exists(path):
            os.mkdirs(path)
        
        f = os.path.join(path, file_name)
        torch.save(self.state_dict(), f)

class Trainer:
    def __init__(self, model, learn_rate, gamma):
        self.learn_rate = learn_rate
        self.gamma = gamma
        self.model = model
        self.optimizer = optim.Adam(model.parameters(), lr=learn_rate)
        self.criterion = nn.MSELoss()

    