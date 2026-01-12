import torch.nn as nn

class MultiHeadBERT(nn.Module):
    def __init__(self, base_model, num_scam_types: int, dropout_prob: float = 0.1):
        super().__init__()
        self.bert = base_model
        self.dropout_scam = nn.Dropout(dropout_prob)
        self.classifier_scam = nn.Linear(self.bert.config.hidden_size, 2)
        self.dropout_type = nn.Dropout(dropout_prob)
        self.classifier_type = nn.Linear(self.bert.config.hidden_size, num_scam_types)

    def forward(self, input_ids, attention_mask, **kwargs):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.pooler_output

        scam_output = self.dropout_scam(pooled_output)
        scam_logits = self.classifier_scam(scam_output)

        type_output = self.dropout_type(pooled_output)
        type_logits = self.classifier_type(type_output)

        return (scam_logits, type_logits)
