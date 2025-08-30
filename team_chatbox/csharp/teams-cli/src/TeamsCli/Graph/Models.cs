using System.Text.Json.Serialization;

namespace TeamsCli.Graph;

public class User
{
    [JsonPropertyName("id")]
    public string? Id { get; set; }
    
    [JsonPropertyName("displayName")]
    public string? DisplayName { get; set; }
    
    [JsonPropertyName("userPrincipalName")]
    public string? UserPrincipalName { get; set; }
}

public class Chat
{
    [JsonPropertyName("id")]
    public string? Id { get; set; }
    
    [JsonPropertyName("topic")]
    public string? Topic { get; set; }
    
    [JsonPropertyName("chatType")]
    public string? ChatType { get; set; }
    
    [JsonPropertyName("lastUpdatedDateTime")]
    public DateTime? LastUpdatedDateTime { get; set; }
}

public class Message
{
    [JsonPropertyName("id")]
    public string? Id { get; set; }
    
    [JsonPropertyName("createdDateTime")]
    public DateTime? CreatedDateTime { get; set; }
    
    [JsonPropertyName("from")]
    public MessageFrom? From { get; set; }
    
    [JsonPropertyName("body")]
    public MessageBody? Body { get; set; }
}

public class MessageFrom
{
    [JsonPropertyName("user")]
    public User? User { get; set; }
}

public class MessageBody
{
    [JsonPropertyName("contentType")]
    public string? ContentType { get; set; }
    
    [JsonPropertyName("content")]
    public string? Content { get; set; }
}

public class ChatListResponse
{
    [JsonPropertyName("value")]
    public Chat[]? Value { get; set; }
    
    [JsonPropertyName("@odata.nextLink")]
    public string? NextLink { get; set; }
}

public class MessageListResponse
{
    [JsonPropertyName("value")]
    public Message[]? Value { get; set; }
    
    [JsonPropertyName("@odata.nextLink")]
    public string? NextLink { get; set; }
    
    [JsonPropertyName("@odata.deltaLink")]
    public string? DeltaLink { get; set; }
}

public class SendMessageRequest
{
    [JsonPropertyName("body")]
    public MessageBody Body { get; set; } = new();
}