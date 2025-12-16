// Bot Discord - 16/12/2025
// Configure seu token na aba de configurações

import { Client, GatewayIntentBits } from 'discord.js';

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
  ],
});

client.once('ready', () => {
  console.log(`Bot online como ${client.user.tag}`);
});

client.on('messageCreate', async (message) => {
  if (message.author.bot) return;
  
  if (message.content === '!ping') {
    await message.reply('Pong! 🏓');
  }
  
  if (message.content === '!oi') {
    await message.reply('Olá! Como posso ajudar? 👋');
  }
});

client.login(process.env.BOT_TOKEN);
