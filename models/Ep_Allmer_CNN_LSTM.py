import torch
import torch.nn as nn
from utilities.match_list_lengths import match_list_lengths

class Ep_Allmer_CNN_LSTM(nn.Module):
    def __init__(self, num_ep_features, num_seq_features, 
                    y_channels, y_kernel_sizes,
                    n_channels, n_kernel_sizes, dropout, 
                    lstm_layer_size, num_lstm_layers, bidirectional):
        
        super(Ep_Allmer_CNN_LSTM, self).__init__()
        self.name = "cnn_lstm"            

        self.y_convs = nn.ModuleList()
        y_in_channels = num_ep_features
        
        y_channels, y_kernel_sizes = match_list_lengths(y_channels, y_kernel_sizes)

        # Y_ji convolutional layers
        for idx, out_channels in enumerate(y_channels):
            self.y_convs.append(
                nn.Conv1d(y_in_channels, out_channels, y_kernel_sizes[idx], stride=1, padding='same')
            )
            y_in_channels = out_channels
        
        
        self.n_convs = nn.ModuleList()
        n_in_channels = num_seq_features
        
        n_channels, n_kernel_sizes = match_list_lengths(n_channels, n_kernel_sizes)
        
        for idx, out_channels in enumerate(n_channels):
            self.n_convs.append(
                nn.Conv1d(n_in_channels, out_channels, n_kernel_sizes[idx], stride=1, padding='same')
            )
            n_in_channels = out_channels

        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        
        self.num_lstm_layers = num_lstm_layers
        self.gru = nn.GRU(input_size=y_channels[-1] + n_channels[-1], hidden_size=lstm_layer_size, num_layers=num_lstm_layers, bidirectional=bidirectional, batch_first=True)
        
        self.final_linear = nn.Linear(lstm_layer_size, 1)
        self.bidirectional = True
        self.final_bidirectional_linear = nn.Linear(lstm_layer_size*2, 1)
        
    def forward(self, Y_ji, N_ji):
        Y_ji = Y_ji.permute(0, 2, 1)  
        N_ji = N_ji.permute(0, 2, 1)
        
        for conv in self.y_convs:
            Y_ji = conv(Y_ji)
            Y_ji = self.relu(Y_ji)
            Y_ji = self.dropout(Y_ji)
        
        for conv in self.n_convs:
            N_ji = conv(N_ji)
            N_ji = self.relu(N_ji)
            N_ji = self.dropout(N_ji)

        x = torch.cat((Y_ji, N_ji), 1)
                    
        x = x.permute(0,2,1)
        x, (h_n, c_n) = self.gru(x)
        if self.bidirectional:
            x = self.final_bidirectional_linear(x)
        else:
            x = self.final_linear(x)
        x = x.squeeze(-1)
            
        return x