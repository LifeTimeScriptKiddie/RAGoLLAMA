namespace TeamsCli.Graph;

public static class Endpoints
{
    public static string Me() => "/me";
    
    public static string MeChats(int? top = null) => 
        top.HasValue ? $"/me/chats?$top={top}" : "/me/chats";
    
    public static string ChatMessages(string chatId) => 
        $"/chats/{chatId}/messages";
    
    public static string ChatMessagesDelta(string chatId) => 
        $"/chats/{chatId}/messages/delta";
    
    public static string PostChatMessage(string chatId) => 
        $"/chats/{chatId}/messages";
}