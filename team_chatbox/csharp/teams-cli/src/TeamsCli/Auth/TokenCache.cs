using Microsoft.Identity.Client;
using Microsoft.Identity.Client.Extensions.Msal;

namespace TeamsCli.Auth;

public static class TokenCache
{
    public static async Task<MsalCacheHelper> CreateAsync()
    {
        var storageProperties = new StorageCreationPropertiesBuilder(
                "msal_cache.dat", 
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData))
            .WithLinuxKeyring("teams-cli", "MsalClientSecret", "microsoft.developer.identityclient.tokencache")
            .WithLinuxUnprotectedFile()
            .WithMacKeyChain("teams-cli", "MsalClientSecret")
            .Build();

        var cacheHelper = await MsalCacheHelper.CreateAsync(storageProperties);
        return cacheHelper;
    }
}