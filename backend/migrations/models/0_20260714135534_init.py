from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "conversations" (
    "id" UUID NOT NULL PRIMARY KEY,
    "title" VARCHAR(80) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS "messages" (
    "id" UUID NOT NULL PRIMARY KEY,
    "role" VARCHAR(16) NOT NULL,
    "content" TEXT NOT NULL,
    "position" INT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL,
    "conversation_id" UUID NOT NULL REFERENCES "conversations" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_messages_convers_f85232" UNIQUE ("conversation_id", "position")
);
CREATE INDEX IF NOT EXISTS "idx_messages_convers_f85232" ON "messages" ("conversation_id", "position");
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "eJztmGtv2jAUhv9KlE+ttFVAKUPTNCmldGUtMJV0q1pVkYkNWA02TZxR1PHfZzv3G4WudI"
    "D6BYVziZ3n2Dmv86SOKUSWc9Cg5DeyHcAwJepn5UklYIz4Ra7/g6KCySTyCgMDfUsmmLFI"
    "6QF9h9nAZNw5AJaDuAkix7TxxB+MuJYljNTkgZgMI5NL8IOLDEaHiI2QzR23d9yMCUSPyA"
    "n+Tu6NAUYWTMwbQzG2tBtsNpG2q6vWyamMFMP1DZNa7phE0ZMZG1EShrsuhgciR/iGiCAb"
    "MARjjyFm6T92YPJmzA3MdlE4VRgZIBoA1xIw1C8Dl5iCgSJHEj/Vr/7UYmGG0enqRq+pG4"
    "a6AjteB8EdEyZAPc29+0ZApFUVAzTOtMu9w9q+REAdNrSlU+JS5zIRMOClSugRZYYZf/wM"
    "6MYI2Pmgw4QUaz7Vl1AODBHmaImFADtoqpgjwNaFVh2DR8NCZMhG/G+9tAD1T+1S0q6XJG"
    "3K94W3azq+pyJdAnoE2bSRQGJ4T5AkfcI9DI9RPu1kZgo59FMPgot1FSAAuQ70/AFhl1gz"
    "f4MtQK+32s2errV/iOHGjvNgSX6a3hSeirTOUta9WqpM4U2UXy39TBF/lZtup5neOmGcfq"
    "OKOQGXUYPQqQFg7F0QWANqiaq7E/jCqicz36u+KVUPGMXKLmcvetjgPvZ+FYY+MO+nwIZG"
    "whPry8hxwBA52cVx7Geenl8iK2zYqWXgt/W2d5ctXAPzYNUH1jhNWqFFOLOucWWctgDCoU"
    "B/bDFSCleOQIqRLNZG8aK9riy6Teguf2FieX2XkkzPhb7Lqf8mp2y6mpoK4t9OTK3zrZ6Q"
    "UeXaEjKqnH5TRzJKuFIyihKGSE431dEjK9BPUcpOIF7UKJvXeqJHBij32tr1fqJPXnQ734"
    "LwGPrGRfc4hTx8sWSYt0gB8nhKijn2KrFlzFXZLz5WytVP1fphrVrnIXKioeXTgrK0Ovr7"
    "aWDHdeEyp4F4yzZWa8Y5qa/ZmTf3lfZMI87I7nzaWdSn1EZ4SM7RTAJv8fkAYuY14oKPZ9"
    "uJOCO1udkG01As5i00fsEJIObpGK3X0E6a6rz4fLNO8a4hG5sjNUe7+56F0h1EMRvzPbOw"
    "iebu8pz26Vfx34T3xvfOYr0tlmvuFi+W3LGUnZCESdVdOTpaQnbzqELdLX1JxSI21QqE/f"
    "AdpFsuLfNtmEcVn2pK2a/DRcea771uZ9VjDcQmU/4oFna2UWovgCtgLD7epE8yKdEgbnCc"
    "pxrespnN/wLUMeUY"
)
