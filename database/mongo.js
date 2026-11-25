// =============================================================
// Script do MongoDB - Petshop
// Como executar: veja o README.md
// =============================================================

db.atendimentos.drop();

// -------------------------------------------------------------
// COLEÇÃO atendimentos (ficha / prontuário de cada atendimento)
// O $jsonSchema faz o MongoDB recusar documentos fora das regras.
// -------------------------------------------------------------
db.createCollection("atendimentos", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      title: "Ficha de atendimento do pet",

      // Campos obrigatórios
      required: ["pet_id", "data", "tipo"],

      properties: {
        // Liga com pets.id do PostgreSQL
        pet_id: {
          bsonType: "int",
          minimum: 1,
          description: "obrigatório: id do pet no PostgreSQL (inteiro)"
        },
        data: {
          bsonType: "date",
          description: "obrigatório: data do atendimento"
        },
        // enum: só aceita estes valores
        tipo: {
          enum: ["banho", "tosa", "consulta", "vacina"],
          description: "obrigatório: banho, tosa, consulta ou vacina"
        },
        // minimum / maximum
        peso_kg: {
          bsonType: "number",
          minimum: 0.1,
          maximum: 150,
          description: "peso entre 0.1 e 150 kg"
        },
        // pattern (expressão regular): exatamente 15 dígitos
        microchip: {
          bsonType: "string",
          pattern: "^[0-9]{15}$",
          description: "microchip com exatamente 15 dígitos"
        },
        vacinas: {
          bsonType: "array",
          items: {
            bsonType: "object",
            required: ["nome", "lote"],
            properties: {
              nome: { bsonType: "string", minLength: 2 },
              lote: { bsonType: "string", minLength: 1 }
            }
          },
          description: "lista de vacinas aplicadas: { nome, lote }"
        },
        // maxLength
        observacoes: {
          bsonType: "string",
          maxLength: 500,
          description: "texto livre de até 500 caracteres"
        }
      }
    }
  }
});

// -------------------------------------------------------------
// ÍNDICE em pet_id
// A busca mais comum é "histórico deste pet", e pet_id é o campo
// usado na integração com o PostgreSQL. Sem índice, o MongoDB
// teria que ler a coleção inteira (COLLSCAN) a cada busca.
// -------------------------------------------------------------
db.atendimentos.createIndex({ pet_id: 1 }, { name: "idx_pet_id" });

// -------------------------------------------------------------
// DOCUMENTOS DE EXEMPLO
// pet_id 1 a 5 = pets do postgres.sql. As datas são relativas a
// hoje, igual ao postgres.sql (os atendimentos de hoje são os
// agendamentos concluídos lá).
// -------------------------------------------------------------
function diasAtras(dias, hora) {
  const d = new Date();
  d.setDate(d.getDate() - dias);
  d.setHours(hora, 0, 0, 0);
  return d;
}

db.atendimentos.insertMany([
  // Thor (pet 1)
  {
    pet_id: 1, data: diasAtras(60, 10), tipo: "vacina",
    peso_kg: 31.2, microchip: "985112003456789",
    vacinas: [{ nome: "V10", lote: "A2391" }, { nome: "Antirrábica", lote: "R7710" }],
    observacoes: "Reforço anual. Sem reação."
  },
  { pet_id: 1, data: diasAtras(0, 8), tipo: "banho", peso_kg: 32.0 },
  {
    pet_id: 1, data: diasAtras(0, 9), tipo: "consulta", peso_kg: 32.0,
    observacoes: "Coceira na orelha esquerda. Receitado limpador auricular."
  },

  // Mia (pet 2)
  {
    pet_id: 2, data: diasAtras(30, 15), tipo: "vacina", peso_kg: 3.9,
    vacinas: [{ nome: "V4 Felina", lote: "F1203" }]
  },
  {
    pet_id: 2, data: diasAtras(0, 10), tipo: "consulta", peso_kg: 4.1,
    observacoes: "Check-up de rotina. Tudo normal."
  },

  // Bob (pet 3) - tosa sem nada extra: o documento só tem o necessário
  { pet_id: 3, data: diasAtras(0, 11), tipo: "tosa" },

  // Luna (pet 4)
  {
    pet_id: 4, data: diasAtras(45, 9), tipo: "vacina",
    peso_kg: 6.5, microchip: "985112009876543",
    vacinas: [{ nome: "V10", lote: "A2391" }]
  }
]);

// -------------------------------------------------------------
// DEMONSTRAÇÃO: documento inválido (para a apresentação)
// tipo fora do enum, peso acima do máximo e microchip com letras.
// O try/catch mostra o erro sem interromper o script.
// -------------------------------------------------------------
try {
  db.atendimentos.insertOne({
    pet_id: 1,
    data: new Date(),
    tipo: "hospedagem",
    peso_kg: 200,
    microchip: "ABC123"
  });
  print("ERRO: o documento inválido foi aceito!");
} catch (e) {
  print("Documento inválido rejeitado pela validação: " + e.message);
}

print("Atendimentos cadastrados: " + db.atendimentos.countDocuments());
