/*
  Warnings:

  - You are about to drop the column `embedding` on the `content_chunks` table. All the data in the column will be lost.

*/
-- AlterTable
ALTER TABLE "content_chunks" DROP COLUMN "embedding";
